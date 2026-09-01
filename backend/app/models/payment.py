from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class PaystackPayment(Base):
    __tablename__ = "paystack_payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reference = Column(String(100), unique=True, nullable=False, index=True)
    amount = Column(Numeric(14, 2), nullable=False)
    status = Column(String(20), nullable=False, default="initialized")  # initialized, success, failed
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User")