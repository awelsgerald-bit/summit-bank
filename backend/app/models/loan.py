from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    principal_amount = Column(Numeric(14, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False, default=10.00)  # % flat, e.g. 10.00 = 10%
    term_months = Column(Integer, nullable=False)
    purpose = Column(String(255), nullable=True)

    total_repayable = Column(Numeric(14, 2), nullable=True)  # principal + interest, set on approval
    outstanding_balance = Column(Numeric(14, 2), nullable=True)  # decreases as repayments come in

    status = Column(String(20), nullable=False, default="pending")  # pending, approved, rejected, repaid
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="loans")