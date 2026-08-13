from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.models.user import User


def list_pending_transactions(db: Session) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.status == "pending")
        .order_by(Transaction.timestamp.asc())
        .all()
    )


def approve_transaction(db: Session, transaction_id: int) -> Transaction:
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if tx.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Transaction is already {tx.status}")

    if tx.transaction_type == TransactionType.DEPOSIT:
        receiver = db.query(User).filter(User.id == tx.receiver_id).with_for_update().first()
        receiver.balance = receiver.balance + tx.amount

    elif tx.transaction_type == TransactionType.WITHDRAWAL:
        sender = db.query(User).filter(User.id == tx.sender_id).with_for_update().first()
        if tx.amount > sender.balance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot approve: user no longer has sufficient balance",
            )
        sender.balance = sender.balance - tx.amount

    elif tx.transaction_type == TransactionType.TRANSFER:
        sender = db.query(User).filter(User.id == tx.sender_id).with_for_update().first()
        receiver = db.query(User).filter(User.id == tx.receiver_id).with_for_update().first()
        if tx.amount > sender.balance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot approve: sender no longer has sufficient balance",
            )
        sender.balance = sender.balance - tx.amount
        receiver.balance = receiver.balance + tx.amount

    tx.status = "approved"
    db.commit()
    db.refresh(tx)
    return tx


def reject_transaction(db: Session, transaction_id: int) -> Transaction:
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if tx.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Transaction is already {tx.status}")

    tx.status = "rejected"
    db.commit()
    db.refresh(tx)
    return tx