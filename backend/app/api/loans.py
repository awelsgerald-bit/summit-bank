from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.loan import LoanApplicationCreate, LoanResponse, RepaymentRequest
from app.services import loan_service

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.post("/apply", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def apply_for_loan(
    payload: LoanApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return loan_service.apply_for_loan(db, current_user, payload.principal_amount, payload.term_months, payload.purpose)


@router.get("", response_model=list[LoanResponse])
def get_my_loans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return loan_service.list_my_loans(db, current_user)


@router.get("/{loan_id}", response_model=LoanResponse)
def get_loan(
    loan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return loan_service.get_my_loan(db, current_user, loan_id)


@router.post("/{loan_id}/repay", response_model=LoanResponse)
def repay_loan(
    loan_id: int,
    payload: RepaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return loan_service.repay_loan(db, current_user, loan_id, payload.amount)