import base64
import binascii
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import AvatarUpdate, PasswordChange, ProfileUpdate, UserResponse
from app.services import fixed_deposit_service

router = APIRouter(prefix="/account", tags=["Account"])

MAX_AVATAR_BYTES = 200 * 1024
_AVATAR_RE = re.compile(r"^data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/]+={0,2})$")
# The first bytes of each allowed image type, so a renamed file cannot slip through.
_MAGIC = {
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpeg": (b"\xff\xd8\xff",),
    "webp": (b"RIFF",),
}


@router.get("/profile", response_model=UserResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fixed_deposit_service.credit_matured_deposits(db, current_user)
    return current_user


@router.get("/balance")
def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fixed_deposit_service.credit_matured_deposits(db, current_user)
    return {
        "account_number": current_user.account_number,
        "balance": current_user.balance,
    }


@router.patch("/profile", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Edit name and phone number. Email, balance and account number cannot be changed here."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()
    if payload.phone_number is not None:
        current_user.phone_number = payload.phone_number.strip()
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/change-password")
def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    if payload.new_password == payload.current_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose a different password")
    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password changed"}


@router.put("/avatar", response_model=UserResponse)
def set_avatar(
    payload: AvatarUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    match = _AVATAR_RE.match(payload.image.strip())
    if match is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use a PNG, JPEG or WebP image")
    kind, encoded = match.group(1), match.group(2)
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The image could not be read")
    if len(raw) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image is too large (max 200 KB)")
    if not raw.startswith(_MAGIC[kind]) or (kind == "webp" and raw[8:12] != b"WEBP"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The file is not a real image")
    current_user.avatar = f"data:image/{kind};base64,{encoded}"
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/avatar", response_model=UserResponse)
def remove_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.avatar = None
    db.commit()
    db.refresh(current_user)
    return current_user
