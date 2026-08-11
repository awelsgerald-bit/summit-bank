from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = (UniqueConstraint("user_id", "currency", name="uq_user_currency"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    currency = Column(String(10), nullable=False)  # e.g. "BTC"
    balance = Column(Numeric(20, 8), nullable=False, default=0)  # 8 decimals for crypto precision
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="wallets")