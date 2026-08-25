from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.card import CardApplicationResponse
from app.services import card_service
from app.schemas.loan import LoanResponse
from app.services import loan_service
from app.schemas.admin import AdminTransactionResponse, AdminUserResponse
from app.services import admin_service
from app.database import get_db
from app.dependencies import require_admin
from app.models.transaction import Transaction
from app.models.user import User
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


@router.get("/transactions/pending", response_model=list[AdminTransactionResponse])
def get_pending_transactions(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    pending = admin_service.list_pending_transactions(db)
    return [_to_receipt(t) for t in pending]

@router.get("/loans/pending", response_model=list[LoanResponse])
def get_pending_loans(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return loan_service.list_pending_loans(db)


@router.post("/loans/{loan_id}/approve", response_model=LoanResponse)
def approve_loan(
    loan_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return loan_service.approve_loan(db, loan_id)


@router.post("/loans/{loan_id}/reject", response_model=LoanResponse)
def reject_loan(
    loan_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return loan_service.reject_loan(db, loan_id)

@router.get("/transactions/{transaction_id}", response_model=AdminTransactionResponse)
def get_transaction_receipt(
    transaction_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return _to_receipt(tx)


@router.post("/transactions/{transaction_id}/approve", response_model=AdminTransactionResponse)
def approve_transaction(
    transaction_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    tx = admin_service.approve_transaction(db, transaction_id)
    return _to_receipt(tx)


@router.post("/transactions/{transaction_id}/reject", response_model=AdminTransactionResponse)
def reject_transaction(
    transaction_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    tx = admin_service.reject_transaction(db, transaction_id)
    return _to_receipt(tx)


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
        status=tx.status,
    )

@router.get("/cards/pending", response_model=list[CardApplicationResponse])
def get_pending_cards(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return card_service.list_pending_cards(db)


@router.post("/cards/{application_id}/approve", response_model=CardApplicationResponse)
def approve_card(
    application_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return card_service.approve_card(db, application_id)


@router.post("/cards/{application_id}/reject", response_model=CardApplicationResponse)
def reject_card(
    application_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return card_service.reject_card(db, application_id)