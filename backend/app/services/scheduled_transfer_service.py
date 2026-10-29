import calendar
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.scheduled_transfer import ScheduledTransfer, ScheduledTransferRun
from app.models.user import User
from app.services import email_service, transaction_service

# Scheduled and recurring transfers.
#
# Safety rules (each one is covered by a test):
#  * A schedule needs the user's PIN to be created or resumed. Later runs happen without the user,
#    so the PIN given at creation is the authorisation.
#  * A run creates an ordinary PENDING transfer through the normal transfer service. Balance check,
#    fraud check and admin approval all still apply. Nothing here moves money by itself.
#  * AT MOST ONCE per due time. A due time is "claimed" by an atomic compare-and-set on
#    next_run_at, and a unique (schedule, due time) run row backs it up. If the server dies
#    between claiming and sending, that one run is lost and shows as "claimed" in the log; it is
#    never sent twice.
#  * No catch-up bursts. If the server was off for days, only one transfer is made for a
#    recurring schedule and the missed ones are skipped.
#  * A failed run (for example not enough balance) is recorded and the user is emailed. A recurring
#    schedule simply waits for its next time; nothing is retried in a loop.

logger = logging.getLogger("summit_bank.scheduler")

WAT = timezone(timedelta(hours=1))  # Nigeria has no daylight saving
FREQUENCIES = ("once", "daily", "weekly", "monthly")
MAX_OPEN_SCHEDULES = 10
MAX_RUNS_PER_PASS = 100


def _aware(ts: Optional[datetime]) -> Optional[datetime]:
    """SQLite hands datetimes back without a timezone; treat those as UTC."""
    if ts is not None and ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts


def advance(previous: datetime, frequency: str, anchor_day: int) -> datetime:
    previous = _aware(previous)
    if frequency == "daily":
        return previous + timedelta(days=1)
    if frequency == "weekly":
        return previous + timedelta(days=7)
    if frequency == "monthly":
        local = previous.astimezone(WAT)
        year, month = (local.year + 1, 1) if local.month == 12 else (local.year, local.month + 1)
        day = min(anchor_day, calendar.monthrange(year, month)[1])  # 31st -> 30th/28th, then back to 31st
        return local.replace(year=year, month=month, day=day).astimezone(timezone.utc)
    raise ValueError(f"cannot advance a {frequency!r} schedule")


def _next_future(due: datetime, frequency: str, anchor_day: int, now: datetime) -> tuple[datetime, int]:
    """The first occurrence after `now`, and how many were skipped getting there."""
    skipped = 0
    nxt = advance(due, frequency, anchor_day)
    while nxt <= now:
        nxt = advance(nxt, frequency, anchor_day)
        skipped += 1
    return nxt, skipped


# ------------------------------------------------------------------ managing schedules

def create(db: Session, user: User, account: str, amount: Decimal, description: Optional[str],
           frequency: str, first_run_at: datetime, end_at: Optional[datetime]) -> ScheduledTransfer:
    account = account.strip()
    if frequency not in FREQUENCIES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Frequency must be once, daily, weekly or monthly")
    first_run_at = first_run_at if first_run_at.tzinfo else first_run_at.replace(tzinfo=WAT)  # no zone = Nigerian time
    first_run_at = first_run_at.astimezone(timezone.utc)
    now = datetime.now(timezone.utc)
    if first_run_at <= now:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Choose a time in the future")
    if end_at is not None:
        end_at = end_at if end_at.tzinfo else end_at.replace(tzinfo=WAT)
        end_at = end_at.astimezone(timezone.utc)
        if frequency == "once":
            end_at = None
        elif end_at <= first_run_at:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "The end date must be after the first transfer")
    open_count = (
        db.query(ScheduledTransfer)
        .filter(ScheduledTransfer.user_id == user.id, ScheduledTransfer.status.in_(("active", "paused")))
        .count()
    )
    if open_count >= MAX_OPEN_SCHEDULES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"You can have up to {MAX_OPEN_SCHEDULES} scheduled transfers")
    recipient = db.query(User).filter(User.account_number == account).first()
    if recipient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recipient account not found")
    if recipient.id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't schedule a transfer to your own account")

    sched = ScheduledTransfer(
        user_id=user.id, recipient_account_number=account, amount=amount,
        description=(description or "").strip() or None, frequency=frequency,
        anchor_day=first_run_at.astimezone(WAT).day, next_run_at=first_run_at, end_at=end_at,
        status="active", run_count=0,
    )
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched


def list_mine(db: Session, user: User) -> list[ScheduledTransfer]:
    return (
        db.query(ScheduledTransfer)
        .filter(ScheduledTransfer.user_id == user.id)
        .order_by(ScheduledTransfer.created_at.desc(), ScheduledTransfer.id.desc())
        .limit(100)
        .all()
    )


def _get_own(db: Session, user: User, schedule_id: int) -> ScheduledTransfer:
    sched = (
        db.query(ScheduledTransfer)
        .filter(ScheduledTransfer.id == schedule_id, ScheduledTransfer.user_id == user.id)
        .first()
    )
    if sched is None:  # someone else's looks exactly like one that does not exist
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scheduled transfer not found")
    return sched


def pause(db: Session, user: User, schedule_id: int) -> ScheduledTransfer:
    _get_own(db, user, schedule_id)
    # Guarded update: a run that just claimed it wins, and pausing then simply has no effect.
    db.query(ScheduledTransfer).filter(
        ScheduledTransfer.id == schedule_id, ScheduledTransfer.status == "active"
    ).update({"status": "paused"}, synchronize_session=False)
    db.commit()
    return _get_own(db, user, schedule_id)


def resume(db: Session, user: User, schedule_id: int) -> ScheduledTransfer:
    sched = _get_own(db, user, schedule_id)
    if sched.status != "paused":
        raise HTTPException(status.HTTP_409_CONFLICT, "Only a paused transfer can be resumed")
    now = datetime.now(timezone.utc)
    nxt = _aware(sched.next_run_at)
    if nxt <= now:
        if sched.frequency == "once":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "That time has passed. Create a new scheduled transfer.")
        nxt, _ = _next_future(nxt, sched.frequency, sched.anchor_day, now)  # skip what was missed while paused
    end_at = _aware(sched.end_at)
    if end_at is not None and nxt > end_at:
        sched.status = "completed"
    else:
        sched.status = "active"
        sched.next_run_at = nxt
    db.commit()
    db.refresh(sched)
    return sched


def cancel(db: Session, user: User, schedule_id: int) -> ScheduledTransfer:
    _get_own(db, user, schedule_id)
    db.query(ScheduledTransfer).filter(
        ScheduledTransfer.id == schedule_id, ScheduledTransfer.status.in_(("active", "paused"))
    ).update({"status": "cancelled"}, synchronize_session=False)
    db.commit()
    return _get_own(db, user, schedule_id)


def list_runs(db: Session, user: User, schedule_id: int) -> list[ScheduledTransferRun]:
    _get_own(db, user, schedule_id)
    return (
        db.query(ScheduledTransferRun)
        .filter(ScheduledTransferRun.schedule_id == schedule_id)
        .order_by(ScheduledTransferRun.id.desc())
        .limit(20)
        .all()
    )


# ------------------------------------------------------------------ the runner

def run_due(db: Session, now: Optional[datetime] = None, user_id: Optional[int] = None) -> dict:
    """Runs every schedule that is due (optionally only one user's). Safe to call from anywhere,
    as often as you like, from several places at once."""
    now = now or datetime.now(timezone.utc)
    query = db.query(ScheduledTransfer.id, ScheduledTransfer.next_run_at).filter(
        ScheduledTransfer.status == "active", ScheduledTransfer.next_run_at <= now
    )
    if user_id is not None:
        query = query.filter(ScheduledTransfer.user_id == user_id)
    due = query.order_by(ScheduledTransfer.next_run_at).limit(MAX_RUNS_PER_PASS).all()

    summary = {"due": len(due), "created": 0, "failed": 0, "skipped": 0}
    for schedule_id, due_at in due:
        outcome = _run_one(db, schedule_id, due_at, now)
        summary[outcome] += 1
    return summary


def _run_one(db: Session, schedule_id: int, due_at: datetime, now: datetime) -> str:
    sched = db.query(ScheduledTransfer).filter(ScheduledTransfer.id == schedule_id).first()
    if sched is None or sched.status != "active" or sched.next_run_at != due_at:
        db.rollback()
        return "skipped"

    frequency, anchor = sched.frequency, sched.anchor_day
    user_id, account, amount, description = sched.user_id, sched.recipient_account_number, sched.amount, sched.description
    end_at = _aware(sched.end_at)
    due_aware = _aware(due_at)

    if frequency == "once":
        new_next, new_status, skipped_note = due_aware, "completed", None
    else:
        new_next, missed = _next_future(due_aware, frequency, anchor, now)
        new_status = "completed" if (end_at is not None and new_next > end_at) else "active"
        skipped_note = f"{missed} missed time(s) skipped" if missed else None

    # CLAIM: only one caller can change next_run_at away from the value it read.
    claimed = (
        db.query(ScheduledTransfer)
        .filter(ScheduledTransfer.id == schedule_id, ScheduledTransfer.status == "active", ScheduledTransfer.next_run_at == due_at)
        .update(
            {"next_run_at": new_next, "status": new_status, "run_count": ScheduledTransfer.run_count + 1, "last_run_at": now},
            synchronize_session=False,
        )
    )
    if not claimed:
        db.rollback()
        return "skipped"
    run = ScheduledTransferRun(schedule_id=schedule_id, due_at=due_at, outcome="claimed", detail=skipped_note)
    db.add(run)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return "skipped"
    run_id = run.id

    # SEND: an ordinary pending transfer.
    outcome, transaction_id, detail = "failed", None, None
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "The account owner no longer exists")
        tx = transaction_service.transfer(db, user, account, amount, description or "Scheduled transfer")
        outcome, transaction_id = "created", tx.id
    except HTTPException as exc:
        db.rollback()
        detail = str(exc.detail)[:200]
    except Exception:
        db.rollback()
        logger.exception("Scheduled transfer %s crashed", schedule_id)
        detail = "Unexpected error"

    if outcome == "failed" and skipped_note:
        detail = f"{detail}; {skipped_note}"
    elif outcome == "created":
        detail = skipped_note
    db.query(ScheduledTransferRun).filter(ScheduledTransferRun.id == run_id).update(
        {"outcome": outcome, "transaction_id": transaction_id, "detail": detail}, synchronize_session=False
    )
    db.query(ScheduledTransfer).filter(ScheduledTransfer.id == schedule_id).update(
        {"last_status": outcome, "last_error": detail if outcome == "failed" else None}, synchronize_session=False
    )
    db.commit()

    if outcome == "failed":
        _tell_user_it_failed(db, user_id, account, amount, detail)
        return "failed"
    return "created"


def _tell_user_it_failed(db: Session, user_id: int, account: str, amount: Decimal, reason: str) -> None:
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            email_service.send_email(
                user.email,
                "Your scheduled transfer did not go through",
                f"<p>Hello,</p><p>Your scheduled transfer of ₦{amount:,.2f} to account {account} could not be made: "
                f"{reason}.</p><p>If it repeats, it will try again at its next time.</p>",
            )
    except Exception:
        logger.exception("Could not email user %s about a failed scheduled transfer", user_id)
