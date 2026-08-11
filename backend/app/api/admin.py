from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.admin import AdminTransactionResponse, AdminUserResponse
from app.models.exchange_rate import ExchangeRate
from app.schemas.exchange_rate import ExchangeRateResponse, ManualRateRequest


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=list[AdminUserResponse])
def list_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.get("/transactions", response_model=list[AdminTransactionResponse])
def list_all_transactions(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    transactions = (
        db.query(Transaction)
        .order_by(Transaction.timestamp.desc())
        .limit(200)
        .all()
    )
    return [_to_receipt(t) for t in transactions]


@router.get("/transactions/{transaction_id}", response_model=AdminTransactionResponse)
def get_transaction_receipt(
    transaction_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException, status

    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return _to_receipt(tx)


def _to_receipt(tx: Transaction) -> AdminTransactionResponse:
    return AdminTransactionResponse(
        id=tx.id,
        transaction_type=tx.transaction_type,
        amount=tx.amount,
        timestamp=tx.timestamp,
        sender_id=tx.sender_id,
        sender_account_number=tx.sender.account_number if tx.sender else None,
        receiver_id=tx.receiver_id,
        receiver_account_number=tx.receiver.account_number if tx.receiver else None,
        description=tx.description,
    )

@router.put("/rates/{currency}", response_model=ExchangeRateResponse)
def set_manual_rate(
    currency: str,
    payload: ManualRateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    currency = currency.upper()
    rate_row = db.query(ExchangeRate).filter(ExchangeRate.currency == currency).first()

    if rate_row:
        rate_row.rate_usd = payload.rate_usd
        rate_row.source = "manual"
    else:
        rate_row = ExchangeRate(currency=currency, rate_usd=payload.rate_usd, source="manual")
        db.add(rate_row)

    db.commit()
    db.refresh(rate_row)
    return rate_row