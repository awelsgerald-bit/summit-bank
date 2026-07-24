from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.transaction import (
    DepositRequest,
    TransactionResponse,
    TransferRequest,
    WithdrawRequest,
)
from app.services import transaction_service
from app.services.transaction_service import get_transaction_history

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/deposit", response_model=TransactionResponse, status_code=201)
def deposit(
    payload: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return transaction_service.deposit(db, current_user, payload.amount, payload.description)


@router.post("/withdraw", response_model=TransactionResponse, status_code=201)
def withdraw(
    payload: WithdrawRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return transaction_service.withdraw(db, current_user, payload.amount, payload.description)


@router.post("/transfer", response_model=TransactionResponse, status_code=201)
def transfer(
    payload: TransferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return transaction_service.transfer(
        db,
        current_user,
        payload.recipient_account_number,
        payload.amount,
        payload.description,
    )

@router.get("/history", response_model=list[TransactionResponse])
def transaction_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_transaction_history(db, current_user)