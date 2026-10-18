import logging
from typing import NamedTuple, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.strowallet_account import StroWalletAccount
from app.models.strowallet_webhook_event import StroWalletWebhookEvent
from app.models.user import User
from app.services import email_service, fraud_service, strowallet_verification_service, transaction_service

# Step 6: a bank transfer that StroWallet has CONFIRMED (event status "verified") becomes a
# PENDING deposit through the same service every other deposit uses. Nothing is credited here:
# the user's balance only changes when an admin approves the deposit, exactly as for manual and
# card deposits. Approval also writes the ledger entries (dual-write), tagged with the sessionId.
#
# Exactly-once: the event row is locked while the deposit is created, the event and the deposit
# are linked in ONE commit, and strowallet_webhook_events.transaction_id is unique. A repeat
# webhook, a retry, or two overlapping runs can therefore never produce a second deposit.

logger = logging.getLogger("summit_bank.strowallet")

# States in which a webhook (or a repeat of one) is still worth processing. "verified" is here so
# a verified event whose deposit was never created (crash, deploy) heals on the next delivery.
PROCESSABLE_STATES = strowallet_verification_service.AUTO_STATES + ("verified",)


class DepositResult(NamedTuple):
    outcome: str  # "created" | "skipped" | "not_found"
    transaction_id: Optional[int]
    detail: str


def _hold(db: Session, event: StroWalletWebhookEvent, detail: str) -> DepositResult:
    """Leaves the event "verified" with an explanation: nothing is credited, nothing is lost,
    and a later retry can still create the deposit once the cause is fixed."""
    event.status_detail = detail[:255]
    db.commit()
    logger.warning("StroWallet deposit not created event_id=%s reason=%s", event.id, detail)
    return DepositResult("skipped", None, detail)


def create_pending_deposit(db: Session, event_id: int) -> DepositResult:
    event = (
        db.query(StroWalletWebhookEvent)
        .filter(StroWalletWebhookEvent.id == event_id)
        .with_for_update()
        .first()
    )
    if event is None:
        return DepositResult("not_found", None, "No such event")
    if event.status != "verified":
        db.rollback()  # release the row lock
        return DepositResult("skipped", None, f"Event is {event.status}; only verified events create deposits")
    if event.transaction_id is not None:
        db.rollback()
        return DepositResult("skipped", event.transaction_id, "A deposit already exists for this event")

    account = None
    if event.strowallet_account_id is not None:
        account = db.query(StroWalletAccount).filter(StroWalletAccount.id == event.strowallet_account_id).first()
    if account is None or account.status != "active":
        return _hold(db, event, "No deposit created: the matching account is not active")
    if account.mode != "live":
        # Real money can only arrive on a live account; a sandbox account must never credit anyone.
        return _hold(db, event, "No deposit created: this is a sandbox account")

    # We credit what actually arrived after StroWallet's fees: the net (settled) amount.
    amount = event.settled_amount
    if amount is None or amount <= 0:
        return _hold(db, event, "No deposit created: the event has no usable settled amount")

    user = db.query(User).filter(User.id == account.user_id).first()
    if user is None:
        return _hold(db, event, "No deposit created: the account owner no longer exists")

    # Copy before commit(): commit expires ORM objects.
    session_id = event.session_id
    transaction, reasons = transaction_service.build_pending_deposit(
        db, user, amount, f"Bank transfer via StroWallet (ref {session_id})"
    )
    transaction_id = transaction.id
    flagged = bool(transaction.is_flagged)

    event.transaction_id = transaction_id
    event.status = "deposit_created"
    event.status_detail = f"Pending deposit #{transaction_id} created; awaiting admin approval"
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.warning("StroWallet deposit already linked event_id=%s", event_id)
        return DepositResult("skipped", None, "Another process already created the deposit")

    logger.info("StroWallet pending deposit created event_id=%s transaction_id=%s", event_id, transaction_id)

    if flagged:
        # After the commit and best effort: a mail failure must not undo or hide the deposit.
        try:
            for admin_email in fraud_service.get_admin_emails(db):
                email_service.send_fraud_alert_email(admin_email, transaction_id, "deposit", amount, reasons)
        except Exception:
            logger.exception("Fraud alert email failed for transaction_id=%s", transaction_id)

    return DepositResult("created", transaction_id, "Pending deposit created")


def process_event(db: Session, event_id: int, manual: bool = False):
    """Verify one event with StroWallet and, if it is confirmed, create its pending deposit.
    Returns (VerifyResult, DepositResult or None). Safe to call repeatedly."""
    verify_result = strowallet_verification_service.verify_event(db, event_id, manual=manual)
    if verify_result.status == "verified":
        return verify_result, create_pending_deposit(db, event_id)
    return verify_result, None


def process_event_in_background(event_id: int) -> None:
    """Entry point for FastAPI background tasks: own session, never raises."""
    from app.database import SessionLocal  # imported here so tests need no database engine

    db = None
    try:
        db = SessionLocal()
        process_event(db, event_id)
    except Exception:
        logger.exception("Background processing crashed event_id=%s", event_id)
        if db is not None:
            try:
                db.rollback()
            except Exception:
                pass
    finally:
        if db is not None:
            db.close()
