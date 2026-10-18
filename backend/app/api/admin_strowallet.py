from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.strowallet_webhook_event import StroWalletWebhookEvent
from app.models.user import User
from app.schemas.strowallet import StroWalletEventDetail, StroWalletEventSummary
from app.services import strowallet_deposit_service

router = APIRouter(prefix="/admin/strowallet", tags=["Admin StroWallet"])


def _get_event_or_404(db: Session, event_id: int) -> StroWalletWebhookEvent:
    event = db.query(StroWalletWebhookEvent).filter(StroWalletWebhookEvent.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.get("/events", response_model=list[StroWalletEventSummary])
def list_events(
    status_filter: Optional[str] = Query(default=None, alias="status", max_length=20),
    limit: int = Query(default=50, ge=1, le=200),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(StroWalletWebhookEvent)
    if status_filter:
        query = query.filter(StroWalletWebhookEvent.status == status_filter)
    return query.order_by(StroWalletWebhookEvent.id.desc()).limit(limit).all()


@router.get("/events/{event_id}", response_model=StroWalletEventDetail)
def get_event(
    event_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _get_event_or_404(db, event_id)


@router.post("/events/{event_id}/verify", response_model=StroWalletEventDetail)
def retry_verification(
    event_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Asks StroWallet again about an event that is stuck, unverified or rejected. If StroWallet
    confirms it (or it was already verified but its deposit was never created), a PENDING
    deposit is created for normal admin approval. Nothing is credited here."""
    _get_event_or_404(db, event_id)
    result, _deposit = strowallet_deposit_service.process_event(db, event_id, manual=True)
    if result.outcome == "not_configured":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Verification is not configured on the server.",
        )
    db.expire_all()
    return _get_event_or_404(db, event_id)