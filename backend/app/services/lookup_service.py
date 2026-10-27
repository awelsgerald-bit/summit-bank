import re

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.services import rate_limit

LOOKUPS_PER_MINUTE = 20
_ACCOUNT_RE = re.compile(r"^\d{6,20}$")


def mask_name(full_name: str) -> str:
    """'Ada Okafor Bello' -> 'Ada O*** B***'. Enough for the sender to recognise the person,
    not enough to harvest full names by trying account numbers."""
    parts = [p for p in (full_name or "").split() if p]
    if not parts:
        return "Summit customer"
    if len(parts) == 1:
        word = parts[0]
        return word[:2] + "***" if len(word) > 2 else word[:1] + "***"
    return " ".join([parts[0]] + [p[0] + "***" for p in parts[1:]])


def lookup_account(db: Session, user: User, account_number: str) -> dict:
    account_number = account_number.strip()
    if not _ACCOUNT_RE.match(account_number):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Enter a valid account number")
    if not rate_limit.allow(f"lookup:{user.id}", LOOKUPS_PER_MINUTE, 60):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many lookups. Please wait a minute.")
    target = db.query(User).filter(User.account_number == account_number).first()
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found")
    return {
        "account_number": target.account_number,
        "name": mask_name(target.full_name),
        "is_self": target.id == user.id,
    }
