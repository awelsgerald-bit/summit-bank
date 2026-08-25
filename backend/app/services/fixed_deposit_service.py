from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.fixed_deposit import FixedDeposit
from app.models.user import User

TERM_OPTIONS_DAYS = [30, 90, 180, 365]

# Longer terms earn a better flat rate
RATE_BY_TERM = {
    30: Decimal("3.00"),
    90: Decimal("5.00"),
    180: Decimal("7.00"),
    365: Decimal("10.00"),
}


def create_fixed_deposit(db: Session, user: User, principal: Decimal, term_days: int) -> FixedDeposit:
    if term_days not in TERM_OPTIONS_DAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"term_days must be one of {TERM_OPTIONS_DAYS}",
        )
    if principal > user.balance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance")

    rate = RATE_BY_TERM[term_days]
    payout = principal * (1 + rate / 100)
    matures_at = datetime.now(timezone.utc) + timedelta(days=term_days)

    user.balance = user.balance - principal

    fd = FixedDeposit(
        user_id=user.id,
        principal_amount=principal,
        interest_rate=rate,
        term_days=term_days,
        payout_amount=payout,
        status="active",
        matures_at=matures_at,
    )
    db.add(fd)
    db.commit()
    db.refresh(fd)
    return fd


def list_my_fixed_deposits(db: Session, user: User) -> list[FixedDeposit]:
    return (
        db.query(FixedDeposit)
        .filter(FixedDeposit.user_id == user.id)
        .order_by(FixedDeposit.created_at.desc())
        .all()
    )


def credit_matured_deposits(db: Session, user: User) -> None:
    """
    Checks this user's active fixed deposits and credits any that have matured.
    Called opportunistically whenever the user's profile is loaded — no separate
    scheduler needed, since this runs on every login/dashboard fetch.
    """
    now = datetime.now(timezone.utc)
    matured = (
        db.query(FixedDeposit)
        .filter(
            FixedDeposit.user_id == user.id,
            FixedDeposit.status == "active",
            FixedDeposit.matures_at <= now,
        )
        .with_for_update()
        .all()
    )

    if not matured:
        return

    for fd in matured:
        user.balance = user.balance + fd.payout_amount
        fd.status = "matured"
        fd.matured_at = now

    db.commit()