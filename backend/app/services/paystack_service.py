import hashlib
import hmac
import uuid
from decimal import Decimal

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.payment import PaystackPayment
from app.models.user import User
from app.services import transaction_service

PAYSTACK_BASE_URL = "https://api.paystack.co"


def _headers():
    return {"Authorization": f"Bearer {settings.paystack_secret_key}"}


def initialize_payment(db: Session, user: User, amount: Decimal) -> dict:
    reference = f"sb_{uuid.uuid4().hex[:20]}"

    response = httpx.post(
        f"{PAYSTACK_BASE_URL}/transaction/initialize",
        headers=_headers(),
        json={
            "email": user.email,
            "amount": int(amount * 100),  # Paystack expects the smallest currency unit (kobo)
            "reference": reference,
        },
        timeout=15.0,
    )

    if response.status_code != 200 or not response.json().get("status"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not initialize payment with Paystack",
        )

    data = response.json()["data"]

    payment = PaystackPayment(
        user_id=user.id,
        reference=reference,
        amount=amount,
        status="initialized",
    )
    db.add(payment)
    db.commit()

    return {"authorization_url": data["authorization_url"], "reference": reference}


def verify_signature(raw_body: bytes, signature_header: str) -> bool:
    computed = hmac.new(
        settings.paystack_secret_key.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(computed, signature_header or "")


def credit_payment(db: Session, reference: str) -> PaystackPayment:
    """
    Confirms a Paystack payment (by calling Paystack's verify endpoint directly,
    the source of truth) and, if genuinely successful and not already processed,
    creates the resulting pending deposit transaction. Safe to call multiple
    times for the same reference — already-processed payments are a no-op.
    """
    payment = db.query(PaystackPayment).filter(PaystackPayment.reference == reference).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment reference not found")

    if payment.status == "success":
        return payment  # already processed, avoid double-crediting

    response = httpx.get(
        f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
        headers=_headers(),
        timeout=15.0,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not verify payment with Paystack")

    data = response.json()["data"]

    if data["status"] != "success":
        payment.status = "failed"
        db.commit()
        return payment

    user = db.query(User).filter(User.id == payment.user_id).first()
    transaction = transaction_service.deposit(
        db, user, payment.amount, description=f"Paystack deposit · ref {reference}"
    )

    payment.status = "success"
    payment.transaction_id = transaction.id
    db.commit()
    db.refresh(payment)
    return payment