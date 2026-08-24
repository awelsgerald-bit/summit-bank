from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    beneficiaries = relationship("Beneficiary", back_populates="user")
    account_number = Column(String(20), unique=True, index=True, nullable=False)
    balance = Column(Numeric(14, 2), nullable=False, default=0)
    role = Column(String(20), nullable=False, default="user")  # "user" or "admin"
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    wallets = relationship("Wallet", back_populates="user")
    sent_transactions = relationship(
        "Transaction", foreign_keys="Transaction.sender_id", back_populates="sender"
    )
    received_transactions = relationship(
        "Transaction", foreign_keys="Transaction.receiver_id", back_populates="receiver"
    )
  