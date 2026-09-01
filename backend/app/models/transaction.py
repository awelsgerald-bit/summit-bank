import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, String, Enum, Boolean, Text
from sqlalchemy.orm import relationship

from app.database import Base


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    currency = Column(String(10), nullable=False, default="USD")
    exchange_rate = Column(Numeric(20, 2), nullable=True)  # rate used, only set for BTC transactions
    status = Column(String(20), nullable=False, default="pending")
    is_flagged = Column(Boolean, nullable=False, default=False)
    flag_reasons = Column(Text, nullable=True)

    # Nullable because a deposit has no sender, a withdrawal has no receiver
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    description = Column(String(255), nullable=True)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_transactions")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_transactions")

    