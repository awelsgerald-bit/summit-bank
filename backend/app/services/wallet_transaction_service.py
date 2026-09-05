from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.models.wallet import Wallet
from app.services import exchange_rate_service, wallet_service


def deposit_btc(db: Session, user: User, amount_usd: Decimal, description: str | None) -> Transaction:
    wallet_service.get_wallet(db, user, "BTC")  # raises 404 if none exists

    rate = exchange_rate_service.get_current_rate(db, "BTC")
    converted_amount = amount_usd / rate.rate_usd

    transaction = Transaction(
        transaction_type=TransactionType.DEPOSIT,
        amount=converted_amount,
        currency="BTC",
        exchange_rate=rate.rate_usd,
        receiver_id=user.id,
        description=description or f"BTC deposit — ${amount_usd} @ ${rate.rate_usd}/BTC",
        status="pending",
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def withdraw_btc(db: Session, user: User, amount_btc: Decimal, description: str | None) -> Transaction:
    wallet = wallet_service.get_wallet(db, user, "BTC")
    if amount_btc > wallet.balance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient BTC balance")

    rate = exchange_rate_service.get_current_rate(db, "BTC")

    transaction = Transaction(
        transaction_type=TransactionType.WITHDRAWAL,
        amount=amount_btc,
        currency="BTC",
        exchange_rate=rate.rate_usd,
        sender_id=user.id,
        description=description or f"BTC withdrawal — converts to ${amount_btc * rate.rate_usd:.2f}",
        status="pending",
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def transfer_btc(
    db: Session, sender: User, recipient_account_number: str, amount_btc: Decimal, description: str | None
) -> Transaction:
    sender_wallet = wallet_service.get_wallet(db, sender, "BTC")
    if amount_btc > sender_wallet.balance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient BTC balance")

    recipient = db.query(User).filter(User.account_number == recipient_account_number).first()
    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient account not found")
    if recipient.id == sender.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot transfer to your own account")

    recipient_wallet = db.query(Wallet).filter(Wallet.user_id == recipient.id, Wallet.currency == "BTC").first()
    if not recipient_wallet:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recipient does not have a BTC wallet")

    transaction = Transaction(
        transaction_type=TransactionType.TRANSFER,
        amount=amount_btc,
        currency="BTC",
        sender_id=sender.id,
        receiver_id=recipient.id,
        description=description or "BTC transfer",
        status="pending",
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction