"""QR code transfers between Summit Bank accounts.

What is in a QR code: a short signed identifier, never an account number, a balance, a password or
a PIN.
    SBQ1:S:<user id>:<signature>     static  - permanently tied to one account
    SBQ1:D:<code>:<signature>        dynamic - one payment request (optional amount and reference)
"SBQ1" is the version; the signature is an HMAC over the version, the kind and the id, made with
the server's secret key, so a code cannot be forged or edited. Scanning it only tells the server
WHO to look up; the recipient's name and account number come from the database.

Rules for a payment (each is covered by a test):
  * needs login AND the transaction PIN (done by the endpoint) AND an Idempotency-Key
  * the same key sent again returns the first receipt and moves no money; the same key with
    different details is refused
  * both accounts are locked in a fixed order, the balance is re-checked under the lock, and the
    debit, the credit, both ledger entries and the transaction row are saved in ONE commit
  * per-payment and per-day limits (settings); inactive accounts cannot send or receive
  * a payment the fraud rules flag is NOT settled: it waits for admin approval and no money moves
    until then (admin approval then moves it and writes the ledger entries)
"""
import hashlib
import hmac
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
from decimal import ROUND_DOWN, Decimal, InvalidOperation
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.qr import QrPaymentRequest, QrTransfer
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.services import email_service, fraud_service, ledger_service, rate_limit

logger = logging.getLogger("summit_bank.qr")

VERSION = "1"
BANK_NAME = "Summit Bank"
WAT = timezone(timedelta(hours=1))
_KEY_RE = re.compile(r"^[A-Za-z0-9_\-]{8,64}$")
_PAYLOAD_RE = re.compile(r"^SBQ(\d+):([SD]):([A-Za-z0-9_\-]{1,24}):([0-9a-f]{20})$")
MAX_REQUEST_MINUTES = 7 * 24 * 60


def _bad(code: int, message: str) -> HTTPException:
    return HTTPException(status_code=code, detail=message)


def _aware(ts: Optional[datetime]) -> Optional[datetime]:
    if ts is not None and ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts


# ------------------------------------------------------------------ the code itself

def _sign(kind: str, ident: str) -> str:
    message = f"v{VERSION}:{kind}:{ident}".encode()
    return hmac.new(settings.secret_key.encode(), message, hashlib.sha256).hexdigest()[:20]


def static_payload(user: User) -> str:
    return f"SBQ{VERSION}:S:{user.id}:{_sign('S', str(user.id))}"


def dynamic_payload(code: str) -> str:
    return f"SBQ{VERSION}:D:{code}:{_sign('D', code)}"


def parse_payload(raw: str) -> tuple[str, str]:
    """Returns (kind, id) for a genuine Summit Bank code, or raises 400."""
    text = (raw or "").strip()
    match = _PAYLOAD_RE.match(text) if len(text) <= 80 else None
    if not match or match.group(1) != VERSION:
        raise _bad(400, "That is not a valid Summit Bank QR code.")
    _, kind, ident, signature = match.groups()
    if not hmac.compare_digest(signature, _sign(kind, ident)):
        raise _bad(400, "That is not a valid Summit Bank QR code.")
    return kind, ident


# ------------------------------------------------------------------ looking up who gets paid

def _recipient_view(user: User) -> dict:
    return {"full_name": user.full_name, "account_number": user.account_number, "bank_name": BANK_NAME}


def _find_target(db: Session, payload: str, lock: bool = False) -> tuple[User, Optional[QrPaymentRequest]]:
    kind, ident = parse_payload(payload)
    request = None
    if kind == "S":
        recipient = db.query(User).filter(User.id == int(ident)).first() if ident.isdigit() else None
    else:
        query = db.query(QrPaymentRequest).filter(QrPaymentRequest.code == ident)
        request = (query.with_for_update() if lock else query).first()
        if request is None:
            raise _bad(404, "This payment request no longer exists.")
        recipient = db.query(User).filter(User.id == request.user_id).first()
    if recipient is None:
        raise _bad(404, "This QR code does not belong to an account.")
    return recipient, request


def _check_request_usable(request: Optional[QrPaymentRequest]) -> None:
    if request is None:
        return
    if request.status == "paid":
        raise _bad(409, "This payment request has already been paid.")
    if request.status == "cancelled":
        raise _bad(410, "This payment request was cancelled.")
    if _aware(request.expires_at) <= datetime.now(timezone.utc):
        raise _bad(410, "This payment request has expired.")


def _check_parties(sender: User, recipient: User) -> None:
    if not sender.is_active:
        raise _bad(403, "Your account is not active. Please contact support.")
    if not recipient.is_active:
        raise _bad(400, "This account cannot receive payments right now.")
    if recipient.id == sender.id:
        raise _bad(400, "You cannot pay your own QR code.")


def resolve(db: Session, sender: User, payload: str) -> dict:
    """What the scanner shows before any money moves."""
    if not rate_limit.allow(f"qr-resolve:{sender.id}", 40, 60):
        raise _bad(429, "Too many scans. Wait a minute and try again.")
    try:
        recipient, request = _find_target(db, payload)
        _check_request_usable(request)
        _check_parties(sender, recipient)
    except HTTPException as exc:
        logger.info("QR resolve refused for user %s: %s", sender.id, exc.detail)
        raise
    return {
        "kind": "dynamic" if request else "static",
        "recipient": _recipient_view(recipient),
        "request": _request_view(request) if request else None,
        "limits": {"per_transfer": str(settings.qr_transfer_max_amount)},
    }


# ------------------------------------------------------------------ dynamic payment requests

def _request_view(request: QrPaymentRequest) -> dict:
    expires = _aware(request.expires_at)
    state = request.status
    if state == "open" and expires <= datetime.now(timezone.utc):
        state = "expired"
    return {
        "id": request.id,
        "amount": str(request.amount) if request.amount is not None else None,
        "reference": request.reference,
        "note": request.note,
        "status": state,
        "expires_at": expires.isoformat(),
        "payload": dynamic_payload(request.code),
    }


def create_request(db: Session, user: User, amount: Optional[Decimal], reference: Optional[str],
                   note: Optional[str], expires_minutes: int) -> dict:
    if not user.is_active:
        raise _bad(403, "Your account is not active. Please contact support.")
    if amount is not None:
        amount = _money(amount)
        if amount > settings.qr_transfer_max_amount:
            raise _bad(400, f"The most one QR payment can be is ₦{settings.qr_transfer_max_amount:,.2f}.")
    now = datetime.now(timezone.utc)
    open_count = (
        db.query(QrPaymentRequest)
        .filter(QrPaymentRequest.user_id == user.id, QrPaymentRequest.status == "open",
                QrPaymentRequest.expires_at > now)
        .count()
    )
    if open_count >= settings.qr_request_max_open:
        raise _bad(400, "You have too many open payment requests. Cancel some first.")
    request = QrPaymentRequest(
        code=secrets.token_urlsafe(12)[:16],
        user_id=user.id,
        amount=amount,
        reference=(reference or "").strip()[:60] or None,
        note=(note or "").strip()[:140] or None,
        status="open",
        expires_at=now + timedelta(minutes=max(1, min(expires_minutes, MAX_REQUEST_MINUTES))),
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return _request_view(request)


def list_requests(db: Session, user: User) -> list[dict]:
    rows = (
        db.query(QrPaymentRequest)
        .filter(QrPaymentRequest.user_id == user.id)
        .order_by(QrPaymentRequest.created_at.desc())
        .limit(50)
        .all()
    )
    return [_request_view(r) for r in rows]


def cancel_request(db: Session, user: User, request_id: int) -> dict:
    request = (
        db.query(QrPaymentRequest)
        .filter(QrPaymentRequest.id == request_id, QrPaymentRequest.user_id == user.id)  # only your own
        .with_for_update()
        .first()
    )
    if request is None:
        raise _bad(404, "Payment request not found.")
    if request.status == "paid":
        raise _bad(409, "This request has already been paid.")
    request.status = "cancelled"
    db.commit()
    return _request_view(request)


# ------------------------------------------------------------------ paying

def _money(value) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise _bad(400, "Enter a valid amount.")
    if not amount.is_finite() or amount <= 0:
        raise _bad(400, "Enter an amount greater than zero.")
    if amount != amount.quantize(Decimal("0.01"), rounding=ROUND_DOWN):
        raise _bad(400, "An amount can have at most 2 decimal places.")
    return amount.quantize(Decimal("0.01"))


def _fingerprint(payload: str, amount: Decimal, narration: str) -> str:
    return hashlib.sha256(f"{payload}|{amount}|{narration}".encode()).hexdigest()


def _sent_today(db: Session, sender_id: int) -> Decimal:
    local_now = datetime.now(WAT)
    start = local_now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    total = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .join(QrTransfer, QrTransfer.transaction_id == Transaction.id)
        .filter(QrTransfer.sender_id == sender_id, QrTransfer.created_at >= start,
                Transaction.status.in_(("approved", "pending")))
        .scalar()
    )
    return Decimal(total or 0)


def _receipt(db: Session, qt: QrTransfer, viewer_id: int, duplicate: bool = False) -> dict:
    tx = qt.transaction
    sender = qt.sender
    receiver = qt.receiver
    state = {"approved": "completed", "pending": "pending_review"}.get(tx.status, tx.status)
    return {
        "reference": qt.reference,
        "transaction_id": tx.id,
        "status": state,
        "direction": "sent" if qt.sender_id == viewer_id else "received",
        "amount": str(Decimal(tx.amount).quantize(Decimal("0.01"))),
        "currency": "NGN",
        "narration": qt.narration,
        "timestamp": _aware(qt.created_at).isoformat(),
        "sender": {"full_name": sender.full_name, "account_number": sender.account_number},
        "recipient": _recipient_view(receiver),
        "duplicate": duplicate,
    }


def transfer(db: Session, sender: User, payload: str, amount, narration: Optional[str],
             idempotency_key: Optional[str]) -> dict:
    if not idempotency_key or not _KEY_RE.match(idempotency_key):
        raise _bad(400, "Missing or invalid Idempotency-Key header (8-64 letters, numbers, - or _).")
    narration = (narration or "").strip()[:140]

    # Resolve first: this also checks the signature, so garbage never reaches the money steps.
    recipient, request = _find_target(db, payload)
    if request is not None and request.amount is not None and amount in (None, ""):
        amount = request.amount
    value = _money(amount)
    fingerprint = _fingerprint(payload.strip(), value, narration)

    existing = (
        db.query(QrTransfer)
        .filter(QrTransfer.sender_id == sender.id, QrTransfer.idempotency_key == idempotency_key)
        .first()
    )
    if existing is not None:
        return _replay(db, existing, fingerprint, sender.id)

    try:
        return _settle(db, sender, recipient, request, payload, value, narration, idempotency_key, fingerprint)
    except IntegrityError:
        # Two identical requests raced: the database let only one in. Answer with the winner.
        db.rollback()
        winner = (
            db.query(QrTransfer)
            .filter(QrTransfer.sender_id == sender.id, QrTransfer.idempotency_key == idempotency_key)
            .first()
        )
        if winner is None:
            logger.exception("QR transfer failed with an integrity error for user %s", sender.id)
            raise _bad(409, "That payment could not be completed. Please try again.")
        return _replay(db, winner, fingerprint, sender.id)


def _replay(db: Session, existing: QrTransfer, fingerprint: str, viewer_id: int) -> dict:
    if existing.request_fingerprint != fingerprint:
        raise _bad(409, "This Idempotency-Key was already used for a different payment.")
    logger.info("QR transfer %s replayed (duplicate request, no money moved)", existing.reference)
    return _receipt(db, existing, viewer_id, duplicate=True)


def _settle(db: Session, sender: User, recipient: User, request: Optional[QrPaymentRequest],
            payload: str, value: Decimal, narration: str, key: str, fingerprint: str) -> dict:
    # Lock both accounts, lowest id first, so two payments can never deadlock each other.
    locked = {
        u.id: u
        for u in db.query(User).filter(User.id.in_([sender.id, recipient.id])).order_by(User.id).with_for_update().all()
    }
    sender_row, recipient_row = locked[sender.id], locked[recipient.id]
    db.refresh(sender_row)
    db.refresh(recipient_row)

    if request is not None:  # re-read under a lock: two people cannot both pay one request
        request = db.query(QrPaymentRequest).filter(QrPaymentRequest.id == request.id).populate_existing().with_for_update().one()
        _check_request_usable(request)
        if request.amount is not None and value != request.amount:
            raise _bad(400, f"This request is for exactly ₦{request.amount:,.2f}.")

    _check_parties(sender_row, recipient_row)

    if value > settings.qr_transfer_max_amount:
        raise _bad(400, f"The most one QR payment can be is ₦{settings.qr_transfer_max_amount:,.2f}.")
    if _sent_today(db, sender_row.id) + value > settings.qr_daily_limit:
        raise _bad(400, f"This would go over your daily QR limit of ₦{settings.qr_daily_limit:,.2f}.")
    if value > sender_row.balance:
        raise _bad(400, "Insufficient balance")

    # Recipient was verified by scanning, so the "new recipient" rule is left out on purpose.
    flagged, reasons = fraud_service.evaluate_transaction(db, sender_row, "transfer", value, None)

    description = f"QR payment to {recipient_row.full_name}" + (f": {narration}" if narration else "")
    tx = Transaction(
        transaction_type=TransactionType.TRANSFER,
        amount=value,
        currency="NGN",
        sender_id=sender_row.id,
        receiver_id=recipient_row.id,
        description=description[:255],
        status="pending" if flagged else "approved",
        is_flagged=flagged,
        flag_reasons="; ".join(reasons) if reasons else None,
    )
    db.add(tx)
    db.flush()

    if not flagged:
        # The debit is a single conditional UPDATE ("only if the balance still covers it"), so even
        # without row locks two payments can never spend the same money twice.
        debit = db.execute(
            update(User).where(User.id == sender_row.id, User.balance >= value)
            .values(balance=User.balance - value).execution_options(synchronize_session=False)
        )
        if debit.rowcount != 1:
            raise _bad(400, "Insufficient balance")
        db.execute(
            update(User).where(User.id == recipient_row.id)
            .values(balance=User.balance + value).execution_options(synchronize_session=False)
        )
        ledger_service.record_transfer(
            db, sender_id=sender_row.id, receiver_id=recipient_row.id, amount=value, currency="NGN",
            reference_transaction_id=tx.id,
        )

    qt = QrTransfer(
        reference="SBQ-" + secrets.token_hex(6).upper(),
        transaction_id=tx.id,
        sender_id=sender_row.id,
        receiver_id=recipient_row.id,
        payment_request_id=request.id if request is not None else None,
        idempotency_key=key,
        request_fingerprint=fingerprint,
        narration=narration or None,
    )
    db.add(qt)
    if request is not None:
        request.status = "paid"
    db.commit()  # debit + credit + ledger + transaction + QR row: all or nothing
    db.refresh(qt)
    db.refresh(sender_row)

    logger.info("QR transfer %s: %s -> %s amount %s %s", qt.reference, sender_row.id, recipient_row.id, value,
                "HELD for admin review" if flagged else "completed")
    if flagged:
        for admin_email in fraud_service.get_admin_emails(db):
            email_service.send_fraud_alert_email(admin_email, tx.id, "transfer", value, reasons)
    return _receipt(db, qt, sender.id)


# ------------------------------------------------------------------ history

def history(db: Session, user: User, limit: int = 100) -> list[dict]:
    rows = (
        db.query(QrTransfer)
        .filter((QrTransfer.sender_id == user.id) | (QrTransfer.receiver_id == user.id))
        .order_by(QrTransfer.created_at.desc(), QrTransfer.id.desc())
        .limit(limit)
        .all()
    )
    return [_receipt(db, r, user.id) for r in rows]


def get_receipt(db: Session, user: User, reference: str) -> dict:
    qt = (
        db.query(QrTransfer)
        .filter(QrTransfer.reference == reference,
                (QrTransfer.sender_id == user.id) | (QrTransfer.receiver_id == user.id))  # only your own
        .first()
    )
    if qt is None:
        raise _bad(404, "Receipt not found.")
    return _receipt(db, qt, user.id)
