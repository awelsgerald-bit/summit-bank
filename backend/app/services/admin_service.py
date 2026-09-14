from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.models.wallet import Wallet
from app.services import ledger_service

def list_pending_transactions(db: Session) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.status == "pending", Transaction.is_flagged == False)  # noqa: E712
        .order_by(Transaction.timestamp.asc())
        .all()
    )


def list_flagged_transactions(db: Session) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.status == "pending", Transaction.is_flagged == True)  # noqa: E712
        .order_by(Transaction.timestamp.asc())
        .all()
    )


def approve_transaction(db: Session, transaction_id: int) -> Transaction:
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    if tx.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Transaction is already {tx.status}")

    if tx.currency == "USD":
        _approve_usd(db, tx)
    elif tx.currency == "BTC":
        _approve_btc(db, tx)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported currency {tx.currency}")

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


def _approve_usd(db: Session, tx: Transaction) -> None:
    if tx.transaction_type == TransactionType.DEPOSIT:
        receiver = db.query(User).filter(User.id == tx.receiver_id).with_for_update().first()
        receiver.balance = receiver.balance + tx.amount

        ledger_service.record_deposit(
            db, user_id=receiver.id, amount=tx.amount, currency="NGN",
            reference_transaction_id=tx.id,
        )

    elif tx.transaction_type == TransactionType.WITHDRAWAL:
        sender = db.query(User).filter(User.id == tx.sender_id).with_for_update().first()
        if tx.amount > sender.balance:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot approve: user no longer has sufficient balance")
        sender.balance = sender.balance - tx.amount

    elif tx.transaction_type == TransactionType.TRANSFER:
        sender = db.query(User).filter(User.id == tx.sender_id).with_for_update().first()
        receiver = db.query(User).filter(User.id == tx.receiver_id).with_for_update().first()
        if tx.amount > sender.balance:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot approve: sender no longer has sufficient balance")
        sender.balance = sender.balance - tx.amount
        receiver.balance = receiver.balance + tx.amount


def _approve_btc(db: Session, tx: Transaction) -> None:
    if tx.transaction_type == TransactionType.DEPOSIT:
        wallet = db.query(Wallet).filter(Wallet.user_id == tx.receiver_id, Wallet.currency == "BTC").with_for_update().first()
        wallet.balance = wallet.balance + tx.amount

        ledger_service.record_deposit(
            db, user_id=tx.receiver_id, amount=tx.amount, currency="BTC",
            reference_transaction_id=tx.id,
        )

    elif tx.transaction_type == TransactionType.WITHDRAWAL:
        wallet = db.query(Wallet).filter(Wallet.user_id == tx.sender_id, Wallet.currency == "BTC").with_for_update().first()
        if tx.amount > wallet.balance:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot approve: user no longer has sufficient BTC balance")
        wallet.balance = wallet.balance - tx.amount
        user = db.query(User).filter(User.id == tx.sender_id).with_for_update().first()
        user.balance = user.balance + (tx.amount * tx.exchange_rate)  # credit USD equivalent, at the rate locked when submitted

    elif tx.transaction_type == TransactionType.TRANSFER:
        sender_wallet = db.query(Wallet).filter(Wallet.user_id == tx.sender_id, Wallet.currency == "BTC").with_for_update().first()
        receiver_wallet = db.query(Wallet).filter(Wallet.user_id == tx.receiver_id, Wallet.currency == "BTC").with_for_update().first()
        if tx.amount > sender_wallet.balance:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot approve: sender no longer has sufficient BTC balance")
        sender_wallet.balance = sender_wallet.balance - tx.amount
        receiver_wallet.balance = receiver_wallet.balance + tx.amount