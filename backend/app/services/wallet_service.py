from decimal import Decimal
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.wallet import Wallet
from app.models.wallet_application import WalletApplication
from app.models.user import User

SUPPORTED_CURRENCIES = {"BTC"}


def list_wallets(db: Session, user: User) -> list[Wallet]:
    return db.query(Wallet).filter(Wallet.user_id == user.id).all()


def apply_for_wallet(db: Session, user: User, currency: str, reason: str | None) -> WalletApplication:
    currency = currency.upper()
    if currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"'{currency}' is not supported.")

    existing_wallet = db.query(Wallet).filter(Wallet.user_id == user.id, Wallet.currency == currency).first()
    if existing_wallet:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"You already have a {currency} wallet.")

    existing_pending = (
        db.query(WalletApplication)
        .filter(WalletApplication.user_id == user.id, WalletApplication.currency == currency, WalletApplication.status == "pending")
        .first()
    )
    if existing_pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"You already have a pending {currency} wallet application.")

    application = WalletApplication(user_id=user.id, currency=currency, reason=reason, status="pending")
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def get_my_wallet_applications(db: Session, user: User) -> list[WalletApplication]:
    return db.query(WalletApplication).filter(WalletApplication.user_id == user.id).order_by(WalletApplication.created_at.desc()).all()


def list_pending_wallet_applications(db: Session) -> list[WalletApplication]:
    return db.query(WalletApplication).filter(WalletApplication.status == "pending").order_by(WalletApplication.created_at.asc()).all()


def approve_wallet_application(db: Session, application_id: int) -> WalletApplication:
    application = db.query(WalletApplication).filter(WalletApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if application.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Application is already {application.status}")

    wallet = Wallet(user_id=application.user_id, currency=application.currency, balance=0)
    db.add(wallet)

    application.status = "approved"
    application.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(application)
    return application


def reject_wallet_application(db: Session, application_id: int) -> WalletApplication:
    application = db.query(WalletApplication).filter(WalletApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if application.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Application is already {application.status}")

    application.status = "rejected"
    application.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(application)
    return application


def get_wallet(db: Session, user: User, currency: str) -> Wallet:
    wallet = db.query(Wallet).filter(Wallet.user_id == user.id, Wallet.currency == currency.upper()).first()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"You don't have a {currency.upper()} wallet.")
    return wallet