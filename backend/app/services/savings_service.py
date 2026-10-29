from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.savings import SavingsMovement, SavingsPot
from app.models.user import User

# Save4Me moves the user's OWN money between their wallet balance and a named pot. Nothing is
# created or destroyed: wallet balance + all pot balances is the same before and after every
# operation. There is no interest on pots.
#
# Every operation locks the user row first and then the pot row (always in that order), reloads
# both from the database, changes both and writes the movement row in ONE commit. Two taps at
# once are therefore handled one after the other, never both against the old balance.

MAX_ACTIVE_POTS = 10


def _lock_user(db: Session, user: User) -> User:
    return db.query(User).filter(User.id == user.id).with_for_update().populate_existing().one()


def _lock_pot(db: Session, user: User, pot_id: int) -> SavingsPot:
    pot = (
        db.query(SavingsPot)
        .filter(SavingsPot.id == pot_id, SavingsPot.user_id == user.id)
        .with_for_update()
        .populate_existing()
        .first()
    )
    # Someone else's pot looks exactly like one that does not exist.
    if pot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Savings pot not found")
    if pot.status != "active":
        raise HTTPException(status.HTTP_409_CONFLICT, "This pot is closed")
    return pot


def list_pots(db: Session, user: User) -> dict:
    pots = (
        db.query(SavingsPot)
        .filter(SavingsPot.user_id == user.id, SavingsPot.status == "active")
        .order_by(SavingsPot.created_at.desc(), SavingsPot.id.desc())
        .all()
    )
    return {"pots": pots, "total_saved": sum((p.balance for p in pots), Decimal("0"))}


def create_pot(db: Session, user: User, name: str, target: Decimal | None) -> SavingsPot:
    active = db.query(SavingsPot).filter(SavingsPot.user_id == user.id, SavingsPot.status == "active").count()
    if active >= MAX_ACTIVE_POTS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"You can have up to {MAX_ACTIVE_POTS} pots")
    pot = SavingsPot(user_id=user.id, name=name.strip(), target_amount=target, balance=Decimal("0"), status="active")
    db.add(pot)
    db.commit()
    db.refresh(pot)
    return pot


def deposit(db: Session, user: User, pot_id: int, amount: Decimal) -> dict:
    locked_user = _lock_user(db, user)
    pot = _lock_pot(db, user, pot_id)
    if amount > locked_user.balance:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Insufficient balance")
    locked_user.balance = locked_user.balance - amount
    pot.balance = pot.balance + amount
    db.add(SavingsMovement(pot_id=pot.id, user_id=user.id, kind="in", amount=amount, pot_balance_after=pot.balance))
    db.commit()
    db.refresh(pot)
    db.refresh(locked_user)
    return {"pot": pot, "wallet_balance": locked_user.balance}


def withdraw(db: Session, user: User, pot_id: int, amount: Decimal) -> dict:
    locked_user = _lock_user(db, user)
    pot = _lock_pot(db, user, pot_id)
    if amount > pot.balance:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That is more than this pot holds")
    pot.balance = pot.balance - amount
    locked_user.balance = locked_user.balance + amount
    db.add(SavingsMovement(pot_id=pot.id, user_id=user.id, kind="out", amount=amount, pot_balance_after=pot.balance))
    db.commit()
    db.refresh(pot)
    db.refresh(locked_user)
    return {"pot": pot, "wallet_balance": locked_user.balance}


def close_pot(db: Session, user: User, pot_id: int) -> dict:
    """Returns whatever the pot holds to the wallet and closes it."""
    locked_user = _lock_user(db, user)
    pot = _lock_pot(db, user, pot_id)
    returned = pot.balance
    if returned > 0:
        locked_user.balance = locked_user.balance + returned
        pot.balance = Decimal("0")
        db.add(SavingsMovement(pot_id=pot.id, user_id=user.id, kind="out", amount=returned, pot_balance_after=Decimal("0")))
    pot.status = "closed"
    pot.closed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(pot)
    db.refresh(locked_user)
    return {"pot": pot, "wallet_balance": locked_user.balance}


def list_movements(db: Session, user: User, pot_id: int) -> list[SavingsMovement]:
    owned = db.query(SavingsPot).filter(SavingsPot.id == pot_id, SavingsPot.user_id == user.id).first()
    if owned is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Savings pot not found")
    return (
        db.query(SavingsMovement)
        .filter(SavingsMovement.pot_id == pot_id)
        .order_by(SavingsMovement.id.desc())
        .limit(100)
        .all()
    )
