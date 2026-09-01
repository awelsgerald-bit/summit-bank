from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.payment import PaystackInitializeRequest, PaystackInitializeResponse, PaystackPaymentResponse
from app.services import paystack_service
from app.core.config import settings

router = APIRouter(prefix="/payments/paystack", tags=["Payments"])


@router.post("/initialize", response_model=PaystackInitializeResponse)
def initialize(
    payload: PaystackInitializeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    callback_url = f"{settings.frontend_url}/payment-callback"
    return paystack_service.initialize_payment(db, current_user, payload.amount, callback_url)


@router.get("/verify/{reference}", response_model=PaystackPaymentResponse)
def verify(
    reference: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return paystack_service.credit_payment(db, reference)


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("x-paystack-signature", "")

    if not paystack_service.verify_signature(raw_body, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    payload = await request.json()
    if payload.get("event") == "charge.success":
        reference = payload["data"]["reference"]
        paystack_service.credit_payment(db, reference)

    return {"received": True}