from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.round2 import SavedPaymentCreate, SavedPaymentResponse
from app.schemas.transaction import TransactionResponse
from app.services import lookup_service, saved_payment_service

router = APIRouter(prefix="/saved-payments", tags=["Saved payments"])


def _present(db: Session, saved) -> dict:
    owner = db.query(User).filter(User.account_number == saved.recipient_account_number).first()
    return {
        "id": saved.id,
        "label": saved.label,
        "recipient_account_number": saved.recipient_account_number,
        "recipient_name": lookup_service.mask_name(owner.full_name) if owner else "Unknown account",
        "amount": saved.amount,
        "description": saved.description,
        "last_paid_at": saved.last_paid_at,
        "created_at": saved.created_at,
    }


@router.get("", response_model=list[SavedPaymentResponse])
def list_saved_payments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [_present(db, s) for s in saved_payment_service.list_saved(db, current_user)]


@router.post("", response_model=SavedPaymentResponse, status_code=status.HTTP_201_CREATED)
def create_saved_payment(
    payload: SavedPaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    saved = saved_payment_service.create_saved(
        db, current_user, payload.label, payload.recipient_account_number, payload.amount, payload.description
    )
    return _present(db, saved)


@router.post("/{saved_id}/pay", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def pay_saved_payment(
    saved_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return saved_payment_service.pay_saved(db, current_user, saved_id)


@router.delete("/{saved_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_payment(
    saved_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    saved_payment_service.delete_saved(db, current_user, saved_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
