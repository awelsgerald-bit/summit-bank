from decimal import Decimal

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.wallet import (
    WalletApplicationCreate, WalletApplicationResponse, WalletResponse,
)
from app.schemas.exchange_rate import ExchangeRateResponse
from app.schemas.transaction import TransactionResponse
from app.services import wallet_service, exchange_rate_service, wallet_transaction_service

router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.get("", response_model=list[WalletResponse])
def get_my_wallets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return wallet_service.list_wallets(db, current_user)


@router.post("/apply", response_model=WalletApplicationResponse, status_code=status.HTTP_201_CREATED)
def apply_for_wallet(
    payload: WalletApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return wallet_service.apply_for_wallet(db, current_user, payload.currency, payload.reason)


@router.get("/applications", response_model=list[WalletApplicationResponse])
def get_my_applications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return wallet_service.get_my_wallet_applications(db, current_user)


@router.get("/rates/{currency}", response_model=ExchangeRateResponse)
def get_rate(currency: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return exchange_rate_service.get_current_rate(db, currency.upper())


@router.post("/BTC/deposit", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def deposit_btc(
    amount_ngn: Decimal,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return wallet_transaction_service.deposit_btc(db, current_user, amount_ngn, None)


@router.post("/BTC/withdraw", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def withdraw_btc(
    amount_btc: Decimal,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return wallet_transaction_service.withdraw_btc(db, current_user, amount_btc, None)


@router.post("/BTC/transfer", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def transfer_btc(
    recipient_account_number: str,
    amount_btc: Decimal,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return wallet_transaction_service.transfer_btc(db, current_user, recipient_account_number, amount_btc, None)