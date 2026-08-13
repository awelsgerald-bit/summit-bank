from fastapi import Query
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.wallet import WalletApplyRequest, WalletResponse
from app.services import wallet_service
from app.schemas.exchange_rate import ExchangeRateResponse
from app.services import exchange_rate_service
from app.models.exchange_rate import ExchangeRate
from app.models.transaction import Transaction, TransactionType
from app.models.wallet import Wallet

router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.get("", response_model=list[WalletResponse])
def get_my_wallets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return wallet_service.list_wallets(db, current_user)


@router.post("/apply", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
def apply_for_wallet(
    payload: WalletApplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return wallet_service.apply_for_wallet(db, current_user, payload.currency)

@router.get("/rates/{currency}", response_model=ExchangeRateResponse)
def get_rate(
    currency: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rate = exchange_rate_service.get_current_rate(db, currency.upper())
    return rate


@router.post("/{currency}/deposit", status_code=status.HTTP_201_CREATED)
def deposit_to_wallet(
    currency: str,
    amount_usd: Decimal = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    currency = currency.upper()
    if amount_usd <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be greater than zero.")

    wallet = (
        db.query(Wallet)
        .filter(Wallet.user_id == current_user.id, Wallet.currency == currency)
        .with_for_update()
        .first()
    )
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"You don't have a {currency} wallet yet.")

    rate = exchange_rate_service.get_current_rate(db, currency)
    converted_amount = amount_usd / rate.rate_usd

    wallet.balance = wallet.balance + converted_amount

    transaction = Transaction(
        transaction_type=TransactionType.DEPOSIT,
        amount=converted_amount,
        currency=currency,
        exchange_rate=rate.rate_usd,
        receiver_id=current_user.id,
        description=f"Deposited ${amount_usd} → {converted_amount:.8f} {currency} @ ${rate.rate_usd}",
    )
    db.add(transaction)
    db.commit()
    db.refresh(wallet)

    return {
        "wallet_id": wallet.id,
        "currency": currency,
        "new_balance": wallet.balance,
        "converted_amount": converted_amount,
        "rate_used": rate.rate_usd,
    }