from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.beneficiary import BeneficiaryCreate, BeneficiaryResponse
from app.services import beneficiary_service

router = APIRouter(prefix="/beneficiaries", tags=["Beneficiaries"])


@router.get("", response_model=list[BeneficiaryResponse])
def get_beneficiaries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return beneficiary_service.list_beneficiaries(db, current_user)


@router.post("", response_model=BeneficiaryResponse, status_code=status.HTTP_201_CREATED)
def create_beneficiary(
    payload: BeneficiaryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return beneficiary_service.add_beneficiary(db, current_user, payload.nickname, payload.account_number)


@router.delete("/{beneficiary_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_beneficiary(
    beneficiary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    beneficiary_service.delete_beneficiary(db, current_user, beneficiary_id)