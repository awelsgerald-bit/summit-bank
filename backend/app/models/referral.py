from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric

from app.database import Base


class ReferralReward(Base):
    """Created once per referred person, when their first qualifying deposit is approved. The
    two bonuses are ordinary PENDING deposits that an admin approves like any other credit."""

    __tablename__ = "referral_rewards"

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referred_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)  # once per person
    qualifying_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    bonus_amount = Column(Numeric(14, 2), nullable=False)
    referrer_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True, unique=True)
    referred_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
