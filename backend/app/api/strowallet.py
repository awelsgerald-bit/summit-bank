from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.strowallet import StroWalletAccountResponse
from app.services import strowallet_service

router = APIRouter(prefix="/strowallet", tags=["StroWallet"])


@router.post("/apply", response_model=StroWalletAccountResponse, status_code=status.HTTP_201_CREATED)
def apply_for_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return strowallet_service.apply_for_account(db, current_user)


@router.get("/my-account", response_model=StroWalletAccountResponse)
def get_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = strowallet_service.get_my_account(db, current_user)
    if not account:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No StroWallet account found. Apply first.")
    return account