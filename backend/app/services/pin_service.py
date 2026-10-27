import re
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User

# The transaction PIN is a second lock on money-moving actions. It is stored only as a bcrypt
# hash, five wrong tries lock it for 15 minutes, and it can only be set or changed by someone who
# also knows the account password.
#
# The API answers with these machine-readable messages; the website turns them into prompts:
#   PIN_REQUIRED | PIN_NOT_SET | PIN_INVALID|<tries left> | PIN_LOCKED|<minutes>

MAX_ATTEMPTS = 5
LOCK_MINUTES = 15
_PIN_RE = re.compile(r"^\d{4,6}$")


def _aware(ts):
    if ts is not None and ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts


def set_pin(db: Session, user: User, password: str, new_pin: str) -> None:
    if not _PIN_RE.match(new_pin or ""):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The PIN must be 4 to 6 digits")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Your account password is incorrect")
    user.transaction_pin_hash = hash_password(new_pin)
    user.pin_failed_attempts = 0
    user.pin_locked_until = None
    db.commit()


def check_pin(db: Session, user: User, pin: str) -> None:
    now = datetime.now(timezone.utc)
    locked_until = _aware(user.pin_locked_until)
    if locked_until is not None and locked_until > now:
        minutes = int((locked_until - now).total_seconds() // 60) + 1
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, f"PIN_LOCKED|{minutes}")

    if pin and _PIN_RE.match(pin) and verify_password(pin, user.transaction_pin_hash):
        if user.pin_failed_attempts or user.pin_locked_until:
            user.pin_failed_attempts = 0
            user.pin_locked_until = None
            db.commit()
        return

    # Count the failure and commit it BEFORE raising, so refusing the request cannot undo it.
    user.pin_failed_attempts = (user.pin_failed_attempts or 0) + 1
    if user.pin_failed_attempts >= MAX_ATTEMPTS:
        user.pin_failed_attempts = 0
        user.pin_locked_until = now + timedelta(minutes=LOCK_MINUTES)
        db.commit()
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, f"PIN_LOCKED|{LOCK_MINUTES}")
    remaining = MAX_ATTEMPTS - user.pin_failed_attempts
    db.commit()
    raise HTTPException(status.HTTP_403_FORBIDDEN, f"PIN_INVALID|{remaining}")
