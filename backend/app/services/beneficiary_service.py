from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.beneficiary import Beneficiary
from app.models.user import User


def list_beneficiaries(db: Session, user: User) -> list[Beneficiary]:
    return (
        db.query(Beneficiary)
        .filter(Beneficiary.user_id == user.id)
        .order_by(Beneficiary.created_at.desc())
        .all()
    )


def add_beneficiary(db: Session, user: User, nickname: str, account_number: str) -> Beneficiary:
    if account_number == user.account_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot add your own account as a beneficiary.",
        )

    recipient_exists = db.query(User).filter(User.account_number == account_number).first()
    if not recipient_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with that account number.",
        )

    existing = (
        db.query(Beneficiary)
        .filter(Beneficiary.user_id == user.id, Beneficiary.account_number == account_number)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This account is already saved as a beneficiary.",
        )

    beneficiary = Beneficiary(user_id=user.id, nickname=nickname, account_number=account_number)
    db.add(beneficiary)
    db.commit()
    db.refresh(beneficiary)
    return beneficiary


def delete_beneficiary(db: Session, user: User, beneficiary_id: int) -> None:
    beneficiary = (
        db.query(Beneficiary)
        .filter(Beneficiary.id == beneficiary_id, Beneficiary.user_id == user.id)
        .first()
    )
    if not beneficiary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beneficiary not found")

    db.delete(beneficiary)
    db.commit()