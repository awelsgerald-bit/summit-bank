from typing import Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_pin_set_and_valid
from app.models.user import User
from app.schemas.qr import PaymentRequestCreate, QrTransferRequest, ResolveRequest
from app.services import qr_service

router = APIRouter(prefix="/qr", tags=["QR transfers"])


@router.get("/me")
def my_qr(current_user: User = Depends(get_current_user)):
    """The signed code for the logged-in person's own account, plus what to print under it."""
    return {
        "payload": qr_service.static_payload(current_user),
        "full_name": current_user.full_name,
        "account_number": current_user.account_number,
        "bank_name": qr_service.BANK_NAME,
        "version": int(qr_service.VERSION),
    }


@router.post("/resolve")
def resolve(payload: ResolveRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return qr_service.resolve(db, current_user, payload.payload)


@router.post("/transfer", status_code=201)
def pay(
    payload: QrTransferRequest,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    current_user: User = Depends(require_pin_set_and_valid),
    db: Session = Depends(get_db),
):
    return qr_service.transfer(db, current_user, payload.payload, payload.amount, payload.narration, idempotency_key)


@router.get("/history")
def history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return qr_service.history(db, current_user)


@router.get("/receipts/{reference}")
def receipt(reference: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return qr_service.get_receipt(db, current_user, reference)


@router.post("/requests", status_code=201)
def create_request(payload: PaymentRequestCreate, current_user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    return qr_service.create_request(db, current_user, payload.amount, payload.reference, payload.note,
                                     payload.expires_minutes)


@router.get("/requests")
def list_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return qr_service.list_requests(db, current_user)


@router.post("/requests/{request_id}/cancel")
def cancel_request(request_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return qr_service.cancel_request(db, current_user, request_id)
