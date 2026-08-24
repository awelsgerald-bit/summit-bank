from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Beneficiary(Base):
    __tablename__ = "beneficiaries"
    __table_args__ = (UniqueConstraint("user_id", "account_number", name="uq_user_beneficiary_account"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nickname = Column(String(100), nullable=False)
    account_number = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="beneficiaries")