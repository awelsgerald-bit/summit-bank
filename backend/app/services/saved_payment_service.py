from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.saved_payment import SavedPayment
from app.models.transaction import Transaction
from app.models.user import User
from app.services import transaction_service

MAX_SAVED_PER_USER = 20
DOUBLE_TAP_SECONDS = 10


def list_saved(db: Session, user: User) -> list[SavedPayment]:
    return (
        db.query(SavedPayment)
        .filter(SavedPayment.user_id == user.id)
        .order_by(SavedPayment.created_at.desc(), SavedPayment.id.desc())
        .all()
    )


def create_saved(db: Session, user: User, label: str, account_number: str, amount: Decimal, description) -> SavedPayment:
    account_number = account_number.strip()
    if db.query(SavedPayment).filter(SavedPayment.user_id == user.id).count() >= MAX_SAVED_PER_USER:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"You can save up to {MAX_SAVED_PER_USER} payments")
    recipient = db.query(User).filter(User.account_number == account_number).first()
    if recipient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recipient account not found")
    if recipient.id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't save a payment to your own account")
    saved = SavedPayment(
        user_id=user.id,
        label=label.strip(),
        recipient_account_number=account_number,
        amount=amount,
        description=(description or "").strip() or None,
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved


def _get_own(db: Session, user: User, saved_id: int) -> SavedPayment:
    saved = (
        db.query(SavedPayment)
        .filter(SavedPayment.id == saved_id, SavedPayment.user_id == user.id)
        .with_for_update()
        .first()
    )
    if saved is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Saved payment not found")
    return saved


def delete_saved(db: Session, user: User, saved_id: int) -> None:
    saved = _get_own(db, user, saved_id)
    db.delete(saved)
    db.commit()


def pay_saved(db: Session, user: User, saved_id: int) -> Transaction:
    """Repeats a saved payment through the normal transfer service. It creates the same pending
    transfer a hand-typed one would (balance check, fraud check, admin approval all apply)."""
    saved = _get_own(db, user, saved_id)  # row lock: two taps at once are handled one after the other
    now = datetime.now(timezone.utc)
    last = saved.last_paid_at
    if last is not None:
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if now - last < timedelta(seconds=DOUBLE_TAP_SECONDS):
            db.rollback()
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "This payment was just sent. Wait a few seconds before repeating it.")

    account, amount, description = saved.recipient_account_number, saved.amount, saved.description
    saved_pk = saved.id
    # Stamp the payment BEFORE sending, in the same locked step that checked it, then commit.
    # A second tap that arrives meanwhile finds the fresh stamp and is refused.
    saved.last_paid_at = now
    db.commit()

    try:
        return transaction_service.transfer(db, user, account, amount, description or "Saved payment")
    except Exception:
        # The transfer did not happen (for example, not enough balance): allow an immediate retry.
        db.rollback()
        db.query(SavedPayment).filter(SavedPayment.id == saved_pk).update({"last_paid_at": last}, synchronize_session=False)
        db.commit()
        raise
