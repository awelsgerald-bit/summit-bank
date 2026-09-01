from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.beneficiary import Beneficiary
from app.models.user import User

VELOCITY_WINDOW_MINUTES = 10
VELOCITY_THRESHOLD = 3  # 3+ transactions from the same user in the window

LARGE_AMOUNT_MULTIPLIER = Decimal("3")  # 3x their usual amount
LARGE_FIRST_TRANSACTION_THRESHOLD = Decimal("5000")  # no history yet, but this big

NEW_RECIPIENT_AMOUNT_THRESHOLD = Decimal("500")  # only flag new recipients for meaningful amounts


def evaluate_transaction(
    db: Session,
    user: User,
    transaction_type: str,
    amount: Decimal,
    recipient_account_number: str | None = None,
) -> tuple[bool, list[str]]:
    reasons = []

    # Rule 1: velocity — many transactions in a short window
    window_start = datetime.now(timezone.utc) - timedelta(minutes=VELOCITY_WINDOW_MINUTES)
    recent_count = (
        db.query(Transaction)
        .filter(Transaction.sender_id == user.id, Transaction.timestamp >= window_start)
        .count()
    )
    if recent_count >= VELOCITY_THRESHOLD:
        reasons.append(f"{recent_count + 1} transactions within {VELOCITY_WINDOW_MINUTES} minutes")

    # Rule 2: unusually large relative to history
    avg_amount = (
        db.query(func.avg(Transaction.amount))
        .filter(Transaction.sender_id == user.id, Transaction.status == "approved")
        .scalar()
    )
    if avg_amount:
        if amount > Decimal(avg_amount) * LARGE_AMOUNT_MULTIPLIER:
            reasons.append(f"Amount is more than {LARGE_AMOUNT_MULTIPLIER}x this user's typical transaction")
    elif amount > LARGE_FIRST_TRANSACTION_THRESHOLD:
        reasons.append("Large amount with no prior transaction history")

    # Rule 3: transfer to a brand-new recipient, for a meaningful amount
    if transaction_type == "transfer" and recipient_account_number and amount > NEW_RECIPIENT_AMOUNT_THRESHOLD:
        is_saved_beneficiary = (
            db.query(Beneficiary)
            .filter(Beneficiary.user_id == user.id, Beneficiary.account_number == recipient_account_number)
            .first()
        )
        recipient_user = db.query(User).filter(User.account_number == recipient_account_number).first()
        has_prior_transfer = False
        if recipient_user:
            has_prior_transfer = (
                db.query(Transaction)
                .filter(
                    Transaction.sender_id == user.id,
                    Transaction.receiver_id == recipient_user.id,
                    Transaction.status == "approved",
                )
                .first()
                is not None
            )
        if not is_saved_beneficiary and not has_prior_transfer:
            reasons.append("First-time transfer to this recipient for a notable amount")

    return (len(reasons) > 0, reasons)


def get_admin_emails(db: Session) -> list[str]:
    admins = db.query(User).filter(User.role == "admin").all()
    return [a.email for a in admins]