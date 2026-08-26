from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.kyc import KYCSubmissionCreate, KYCSubmissionResponse
from app.services import kyc_service

router = APIRouter(prefix="/kyc", tags=["KYC"])


@router.post("/submit", response_model=KYCSubmissionResponse, status_code=status.HTTP_201_CREATED)
def submit_kyc(
    payload: KYCSubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return kyc_service.submit_kyc(db, current_user, payload.model_dump())


@router.get("", response_model=list[KYCSubmissionResponse])
def get_my_kyc(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return kyc_service.get_my_kyc(db, current_user)