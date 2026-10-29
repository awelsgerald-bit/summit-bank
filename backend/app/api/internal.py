import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.services import scheduled_transfer_service

router = APIRouter(prefix="/internal", tags=["Internal"])


@router.api_route("/run-schedules", methods=["GET", "POST"])
def run_schedules(x_cron_token: str = Header(default=""), db: Session = Depends(get_db)):
    """For an outside timer (a free cron service) to call every few minutes. It also wakes a
    sleeping server. Off unless CRON_TOKEN is set; the token is compared in constant time."""
    if not settings.cron_token:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    if not hmac.compare_digest(x_cron_token.encode(), settings.cron_token.encode()):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    return scheduled_transfer_service.run_due(db)
