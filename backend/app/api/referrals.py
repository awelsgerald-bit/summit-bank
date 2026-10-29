from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.round3b import ReferralSummary
from app.services import referral_service

router = APIRouter(prefix="/referrals", tags=["Referrals"])


@router.get("/me", response_model=ReferralSummary)
def my_referrals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return referral_service.summary(db, current_user)
