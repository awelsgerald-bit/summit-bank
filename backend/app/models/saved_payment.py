from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String

from app.database import Base


class SavedPayment(Base):
    """A transfer the user wants to repeat in one tap. It stores only who, how much and why;
    paying it goes through the normal transfer service, so every normal check still applies."""

    __tablename__ = "saved_payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    label = Column(String(60), nullable=False)
    recipient_account_number = Column(String(20), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    description = Column(String(255), nullable=True)
    last_paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
