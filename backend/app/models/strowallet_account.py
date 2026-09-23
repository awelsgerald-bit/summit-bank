from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class StroWalletAccount(Base):
    __tablename__ = "strowallet_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    nuban_account_number = Column(String(20), nullable=True)  # set once StroWallet responds
    bank_name = Column(String(100), nullable=True)
    account_name = Column(String(150), nullable=True)
    strowallet_customer_reference = Column(String(100), nullable=True, unique=True)

    status = Column(String(20), nullable=False, default="pending")  # pending, active, failed, suspended
    failure_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    activated_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="strowallet_account")