from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.card import CardApplicationCreate, CardApplicationResponse
from app.services import card_service

router = APIRouter(prefix="/cards", tags=["Cards"])


@router.post("/apply", response_model=CardApplicationResponse, status_code=status.HTTP_201_CREATED)
def apply_for_card(
    payload: CardApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return card_service.apply_for_card(db, current_user, payload.card_type)


@router.get("", response_model=list[CardApplicationResponse])
def get_my_cards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return card_service.list_my_cards(db, current_user)


@router.post("/{application_id}/freeze", response_model=CardApplicationResponse)
def freeze_card(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return card_service.set_frozen(db, current_user, application_id, True)


@router.post("/{application_id}/unfreeze", response_model=CardApplicationResponse)
def unfreeze_card(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return card_service.set_frozen(db, current_user, application_id, False)
