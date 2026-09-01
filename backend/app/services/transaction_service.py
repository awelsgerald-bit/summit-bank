from decimal import Decimal

from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.services import fraud_service, email_service


def deposit(db: Session, user: User, amount: Decimal, description: str | None) -> Transaction:
    is_flagged, reasons = fraud_service.evaluate_transaction(db, user, "deposit", amount)

    transaction = Transaction(
        transaction_type=TransactionType.DEPOSIT,
        amount=amount,
        currency="USD",
        sender_id=None,
        receiver_id=user.id,
        description=description or "Deposit",
        status="pending",
        is_flagged=is_flagged,
        flag_reasons="; ".join(reasons) if reasons else None,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    if is_flagged:
        for admin_email in fraud_service.get_admin_emails(db):
            email_service.send_fraud_alert_email(admin_email, transaction.id, "deposit", amount, reasons)

    return transaction


def withdraw(db: Session, user: User, amount: Decimal, description: str | None) -> Transaction:
    if amount > user.balance:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Insufficient balance")

    is_flagged, reasons = fraud_service.evaluate_transaction(db, user, "withdrawal", amount)

    transaction = Transaction(
        transaction_type=TransactionType.WITHDRAWAL,
        amount=amount,
        currency="USD",
        sender_id=user.id,
        receiver_id=None,
        description=description or "Withdrawal",
        status="pending",
        is_flagged=is_flagged,
        flag_reasons="; ".join(reasons) if reasons else None,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    if is_flagged:
        for admin_email in fraud_service.get_admin_emails(db):
            email_service.send_fraud_alert_email(admin_email, transaction.id, "withdrawal", amount, reasons)

    return transaction


def transfer(
    db: Session,
    sender: User,
    recipient_account_number: str,
    amount: Decimal,
    description: str | None,
) -> Transaction:
    recipient = db.query(User).filter(User.account_number == recipient_account_number).first()

    if recipient is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Recipient account not found")
    if recipient.id == sender.id:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Cannot transfer to your own account")
    if amount > sender.balance:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Insufficient balance")

    is_flagged, reasons = fraud_service.evaluate_transaction(
        db, sender, "transfer", amount, recipient_account_number
    )

    transaction = Transaction(
        transaction_type=TransactionType.TRANSFER,
        amount=amount,
        currency="USD",
        sender_id=sender.id,
        receiver_id=recipient.id,
        description=description or "Transfer",
        status="pending",
        is_flagged=is_flagged,
        flag_reasons="; ".join(reasons) if reasons else None,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    if is_flagged:
        for admin_email in fraud_service.get_admin_emails(db):
            email_service.send_fraud_alert_email(admin_email, transaction.id, "transfer", amount, reasons)

    return transaction


def get_transaction_history(db: Session, user: User) -> list[Transaction]:
    from sqlalchemy import or_

    return (
        db.query(Transaction)
        .filter(or_(Transaction.sender_id == user.id, Transaction.receiver_id == user.id))
        .order_by(Transaction.timestamp.desc())
        .all()
    )