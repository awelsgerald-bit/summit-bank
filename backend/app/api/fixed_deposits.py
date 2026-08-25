from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.fixed_deposit import FixedDepositCreate, FixedDepositResponse
from app.services import fixed_deposit_service

router = APIRouter(prefix="/fixed-deposits", tags=["Fixed Deposits"])


@router.get("/terms")
def get_term_options():
    return fixed_deposit_service.RATE_BY_TERM


@router.post("", response_model=FixedDepositResponse, status_code=status.HTTP_201_CREATED)
def open_fixed_deposit(
    payload: FixedDepositCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return fixed_deposit_service.create_fixed_deposit(db, current_user, payload.principal_amount, payload.term_days)


@router.get("", response_model=list[FixedDepositResponse])
def get_my_fixed_deposits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return fixed_deposit_service.list_my_fixed_deposits(db, current_user)