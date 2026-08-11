from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.wallet import Wallet
from app.models.user import User

SUPPORTED_CURRENCIES = {"BTC"}


def list_wallets(db: Session, user: User) -> list[Wallet]:
    return db.query(Wallet).filter(Wallet.user_id == user.id).all()


def apply_for_wallet(db: Session, user: User, currency: str) -> Wallet:
    currency = currency.upper()

    if currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{currency}' is not a supported wallet currency.",
        )

    existing = (
        db.query(Wallet)
        .filter(Wallet.user_id == user.id, Wallet.currency == currency)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have a {currency} wallet.",
        )

    wallet = Wallet(user_id=user.id, currency=currency, balance=0)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet