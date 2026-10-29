import logging
import secrets
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.referral import ReferralReward
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.services import lookup_service, transaction_service

# Referrals.
#  * Every user can share a code. A new user can enter it when registering.
#  * When that new user's first deposit of at least REFERRAL_MIN_FIRST_DEPOSIT is APPROVED by an
#    admin, both people get a bonus of REFERRAL_BONUS_AMOUNT.
#  * The bonuses are ordinary PENDING deposits: an admin approves each one (and sees who invited
#    whom in its description), exactly like any other credit. Nothing is credited automatically.
#  * Once per referred person (unique constraint), and a limit per referrer.
#  * A bonus deposit can never trigger another bonus.

logger = logging.getLogger("summit_bank.referrals")

_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no 0/O/1/I/L


def ensure_code(db: Session, user: User) -> str:
    if user.referral_code:
        return user.referral_code
    for _ in range(20):
        code = "SB" + "".join(secrets.choice(_ALPHABET) for _ in range(6))
        if db.query(User).filter(User.referral_code == code).first() is None:
            user.referral_code = code
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                continue
            return code
    raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Could not make a referral code. Try again.")


def find_referrer(db: Session, code: str) -> User:
    referrer = db.query(User).filter(User.referral_code == code.strip().upper()).first()
    if referrer is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That referral code does not exist")
    return referrer


def _bonus_transaction_ids(db: Session) -> set[int]:
    ids = set()
    for a, b in db.query(ReferralReward.referrer_transaction_id, ReferralReward.referred_transaction_id).all():
        ids.update(i for i in (a, b) if i)
    return ids


def on_deposit_approved(db: Session, tx: Transaction):
    """Called after an admin approves a transaction. Creates the two pending bonus deposits when
    this is a qualifying first deposit. Returns the reward, or None when nothing applies."""
    if tx.transaction_type != TransactionType.DEPOSIT or tx.status != "approved" or tx.currency != "NGN":
        return None
    referred = db.query(User).filter(User.id == tx.receiver_id).first()
    if referred is None or referred.referred_by_user_id is None:
        return None
    referrer = db.query(User).filter(User.id == referred.referred_by_user_id).first()
    if referrer is None or referrer.id == referred.id:
        return None
    if tx.amount < settings.referral_min_first_deposit:
        return None
    if tx.id in _bonus_transaction_ids(db):
        return None  # a bonus never triggers another bonus
    if db.query(ReferralReward).filter(ReferralReward.referred_id == referred.id).first() is not None:
        return None
    given = db.query(ReferralReward).filter(ReferralReward.referrer_id == referrer.id).count()
    if given >= settings.referral_max_rewards_per_user:
        return None

    amount = Decimal(settings.referral_bonus_amount)
    if amount <= 0:
        return None
    reward = ReferralReward(
        referrer_id=referrer.id, referred_id=referred.id, qualifying_transaction_id=tx.id, bonus_amount=amount,
    )
    db.add(reward)
    try:
        db.flush()  # the unique referred_id decides races here, before any bonus exists
        bonus_for_referrer, _ = transaction_service.build_pending_deposit(
            db, referrer, amount, f"Referral bonus: {referred.full_name} joined with your code"
        )
        bonus_for_referred, _ = transaction_service.build_pending_deposit(
            db, referred, amount, f"Welcome bonus: you joined with {referrer.full_name}'s referral code"
        )
        reward.referrer_transaction_id = bonus_for_referrer.id
        reward.referred_transaction_id = bonus_for_referred.id
        db.commit()
    except IntegrityError:
        db.rollback()
        return None
    return reward


def _bonus_status(db: Session, transaction_id) -> str:
    if transaction_id is None:
        return "none"
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    return tx.status if tx else "none"


def summary(db: Session, user: User) -> dict:
    code = ensure_code(db, user)
    invited = db.query(User).filter(User.referred_by_user_id == user.id).order_by(User.created_at.desc(), User.id.desc()).all()
    rewards = {r.referred_id: r for r in db.query(ReferralReward).filter(ReferralReward.referrer_id == user.id).all()}
    items, earned = [], Decimal("0")
    for person in invited:
        reward = rewards.get(person.id)
        if reward is None:
            state = "waiting"  # joined, no qualifying deposit approved yet
        else:
            state = _bonus_status(db, reward.referrer_transaction_id)  # pending, approved or rejected
            if state == "approved":
                earned += reward.bonus_amount
        items.append({"name": lookup_service.mask_name(person.full_name), "joined_at": person.created_at, "state": state})
    return {
        "code": code,
        "bonus_amount": settings.referral_bonus_amount,
        "min_first_deposit": settings.referral_min_first_deposit,
        "invited_count": len(invited),
        "earned": earned,
        "items": items,
    }
