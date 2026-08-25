import random
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.card import CardApplication

VALID_CARD_TYPES = {"virtual", "physical"}


def apply_for_card(db: Session, user, card_type: str) -> CardApplication:
    card_type = card_type.lower()
    if card_type not in VALID_CARD_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="card_type must be 'virtual' or 'physical'")

    existing_pending = (
        db.query(CardApplication)
        .filter(CardApplication.user_id == user.id, CardApplication.status == "pending")
        .first()
    )
    if existing_pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have a pending card application")

    application = CardApplication(user_id=user.id, card_type=card_type, status="pending")
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def list_my_cards(db: Session, user) -> list[CardApplication]:
    return (
        db.query(CardApplication)
        .filter(CardApplication.user_id == user.id)
        .order_by(CardApplication.created_at.desc())
        .all()
    )


def _generate_card_number() -> str:
    # Not a real card network BIN — placeholder, prefixed distinctly for a demo app
    digits = "".join(str(random.randint(0, 9)) for _ in range(15))
    number = "4" + digits  # visually looks like a card number, starts with 4 like Visa-style formatting
    return " ".join(number[i:i + 4] for i in range(0, 16, 4))


def list_pending_cards(db: Session) -> list[CardApplication]:
    return (
        db.query(CardApplication)
        .filter(CardApplication.status == "pending")
        .order_by(CardApplication.created_at.asc())
        .all()
    )


def approve_card(db: Session, application_id: int) -> CardApplication:
    application = db.query(CardApplication).filter(CardApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card application not found")
    if application.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Application is already {application.status}")

    now = datetime.now(timezone.utc)
    application.card_number = _generate_card_number()
    application.expiry_month = now.month
    application.expiry_year = now.year + 4
    application.cvv = f"{random.randint(0, 999):03d}"
    application.status = "approved"
    application.approved_at = now

    db.commit()
    db.refresh(application)
    return application


def reject_card(db: Session, application_id: int) -> CardApplication:
    application = db.query(CardApplication).filter(CardApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card application not found")
    if application.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Application is already {application.status}")

    application.status = "rejected"
    db.commit()
    db.refresh(application)
    return application