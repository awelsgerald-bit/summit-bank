from datetime import datetime, timezone

from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.database import Base


class FixedDeposit(Base):
    __tablename__ = "fixed_deposits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    principal_amount = Column(Numeric(14, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False, default=8.00)  # % flat, over the whole term
    term_days = Column(Integer, nullable=False)

    payout_amount = Column(Numeric(14, 2), nullable=False)  # principal + interest, calculated at creation
    status = Column(String(20), nullable=False, default="active")  # active, matured

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    matures_at = Column(DateTime(timezone=True), nullable=False)
    matured_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="fixed_deposits")