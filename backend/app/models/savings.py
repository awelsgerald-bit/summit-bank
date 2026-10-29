from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String

from app.database import Base


class SavingsPot(Base):
    """A Save4Me pot: money the user has set aside from their wallet. It is still the user's
    money, just out of reach of transfers until they move it back."""

    __tablename__ = "savings_pots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(60), nullable=False)
    target_amount = Column(Numeric(14, 2), nullable=True)
    balance = Column(Numeric(14, 2), nullable=False, default=0)
    status = Column(String(10), nullable=False, default="active")  # active, closed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime(timezone=True), nullable=True)


class SavingsMovement(Base):
    """Every move into or out of a pot, so a pot's balance can always be explained."""

    __tablename__ = "savings_movements"

    id = Column(Integer, primary_key=True, index=True)
    pot_id = Column(Integer, ForeignKey("savings_pots.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kind = Column(String(10), nullable=False)  # in, out
    amount = Column(Numeric(14, 2), nullable=False)
    pot_balance_after = Column(Numeric(14, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
