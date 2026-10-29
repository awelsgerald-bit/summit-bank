from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return user 

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_transaction_pin(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Use on actions that move money. A user who has set a PIN must send it in the
    X-Transaction-Pin header; a user who has not set one yet is let through (so nobody is locked
    out the day this ships), and the website nudges them to set one."""
    from app.services import pin_service

    if current_user.transaction_pin_hash is None:
        return current_user
    pin = request.headers.get("X-Transaction-Pin")
    if not pin:
        raise HTTPException(status_code=status.HTTP_428_PRECONDITION_REQUIRED, detail="PIN_REQUIRED")
    pin_service.check_pin(db, current_user, pin)
    return current_user


def require_pin_set_and_valid(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Stricter: for brand-new money features, a PIN must exist and be correct."""
    from app.services import pin_service

    if current_user.transaction_pin_hash is None:
        raise HTTPException(status_code=status.HTTP_428_PRECONDITION_REQUIRED, detail="PIN_NOT_SET")
    pin = request.headers.get("X-Transaction-Pin")
    if not pin:
        raise HTTPException(status_code=status.HTTP_428_PRECONDITION_REQUIRED, detail="PIN_REQUIRED")
    pin_service.check_pin(db, current_user, pin)
    return current_user
