from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/account", tags=["Account"])


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/balance")
def get_balance(current_user: User = Depends(get_current_user)):
    return {
        "account_number": current_user.account_number,
        "balance": current_user.balance,
    }