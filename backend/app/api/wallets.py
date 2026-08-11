from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.wallet import WalletApplyRequest, WalletResponse
from app.services import wallet_service

router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.get("", response_model=list[WalletResponse])
def get_my_wallets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return wallet_service.list_wallets(db, current_user)


@router.post("/apply", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
def apply_for_wallet(
    payload: WalletApplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return wallet_service.apply_for_wallet(db, current_user, payload.currency)