
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
import json

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.strowallet import StroWalletAccountResponse, StroWalletApplyRequest
from app.services import strowallet_service
from app.core.config import settings

router = APIRouter(prefix="/strowallet", tags=["StroWallet"])


@router.post(
    "/apply",
    response_model=StroWalletAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
def apply_for_account(
    payload: Optional[StroWalletApplyRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    phone = payload.phone if payload else None
    return strowallet_service.apply_for_account(db, current_user, phone)


@router.get(
    "/my-account",
    response_model=StroWalletAccountResponse,
)
def get_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = strowallet_service.get_my_account(db, current_user)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No StroWallet account found. Apply first.",
        )

    return account


@router.post("/webhook")
async def strowallet_webhook(
    request: Request,
    token: str = "",
):
    # Reject requests that do not contain our configured shared token.
    if (
        not settings.strowallet_webhook_secret
        or token != settings.strowallet_webhook_secret
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook token",
        )

    # Temporary diagnostic endpoint only.
    # This endpoint MUST NOT credit balances or create transactions.
    raw_body = await request.body()

    try:
        payload = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Log the event for sandbox investigation.
    # Never log the shared token or other credentials.
    print(
        f"[StroWallet Webhook] "
        f"{datetime.now(timezone.utc).isoformat()} — "
        f"{json.dumps(payload)}"
    )

    return {"received": True}
