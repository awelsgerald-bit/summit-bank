from decimal import Decimal
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.loan import Loan
from app.models.user import User

FLAT_INTEREST_RATE = Decimal("10.00")  # 10% flat, applied once for the whole term


def apply_for_loan(db: Session, user: User, principal: Decimal, term_months: int, purpose: str | None) -> Loan:
    loan = Loan(
        user_id=user.id,
        principal_amount=principal,
        interest_rate=FLAT_INTEREST_RATE,
        term_months=term_months,
        purpose=purpose,
        status="pending",
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


def list_my_loans(db: Session, user: User) -> list[Loan]:
    return db.query(Loan).filter(Loan.user_id == user.id).order_by(Loan.created_at.desc()).all()


def get_my_loan(db: Session, user: User, loan_id: int) -> Loan:
    loan = db.query(Loan).filter(Loan.id == loan_id, Loan.user_id == user.id).first()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    return loan


def repay_loan(db: Session, user: User, loan_id: int, amount: Decimal) -> Loan:
    loan = get_my_loan(db, user, loan_id)

    if loan.status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Loan is {loan.status}, not repayable")
    if amount > user.balance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance to make this repayment")
    if amount > loan.outstanding_balance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount exceeds outstanding balance")

    user.balance = user.balance - amount
    loan.outstanding_balance = loan.outstanding_balance - amount

    if loan.outstanding_balance <= 0:
        loan.status = "repaid"

    db.commit()
    db.refresh(loan)
    return loan


# --- Admin-side ---

def list_pending_loans(db: Session) -> list[Loan]:
    return db.query(Loan).filter(Loan.status == "pending").order_by(Loan.created_at.asc()).all()


def approve_loan(db: Session, loan_id: int) -> Loan:
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    if loan.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Loan is already {loan.status}")

    user = db.query(User).filter(User.id == loan.user_id).with_for_update().first()

    total_repayable = loan.principal_amount * (1 + loan.interest_rate / 100)
    loan.total_repayable = total_repayable
    loan.outstanding_balance = total_repayable
    loan.status = "approved"
    loan.approved_at = datetime.now(timezone.utc)

    user.balance = user.balance + loan.principal_amount

    db.commit()
    db.refresh(loan)
    return loan


def reject_loan(db: Session, loan_id: int) -> Loan:
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    if loan.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Loan is already {loan.status}")

    loan.status = "rejected"
    db.commit()
    db.refresh(loan)
    return loan