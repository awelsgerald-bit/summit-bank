from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_pin_set_and_valid
from app.models.user import User
from app.schemas.savings import (
    MovementResponse, PotActionResponse, PotCreate, PotListResponse, PotMove, PotResponse,
)
from app.services import savings_service

router = APIRouter(prefix="/savings", tags=["Save4Me"])


@router.get("/pots", response_model=PotListResponse)
def list_pots(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return savings_service.list_pots(db, current_user)


@router.post("/pots", response_model=PotResponse, status_code=status.HTTP_201_CREATED)
def create_pot(payload: PotCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return savings_service.create_pot(db, current_user, payload.name, payload.target_amount)


@router.post("/pots/{pot_id}/deposit", response_model=PotActionResponse)
def deposit(
    pot_id: int,
    payload: PotMove,
    current_user: User = Depends(require_pin_set_and_valid),
    db: Session = Depends(get_db),
):
    return savings_service.deposit(db, current_user, pot_id, payload.amount)


@router.post("/pots/{pot_id}/withdraw", response_model=PotActionResponse)
def withdraw(
    pot_id: int,
    payload: PotMove,
    current_user: User = Depends(require_pin_set_and_valid),
    db: Session = Depends(get_db),
):
    return savings_service.withdraw(db, current_user, pot_id, payload.amount)


@router.post("/pots/{pot_id}/close", response_model=PotActionResponse)
def close_pot(
    pot_id: int,
    current_user: User = Depends(require_pin_set_and_valid),
    db: Session = Depends(get_db),
):
    return savings_service.close_pot(db, current_user, pot_id)


@router.get("/pots/{pot_id}/movements", response_model=list[MovementResponse])
def movements(pot_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return savings_service.list_movements(db, current_user, pot_id)
