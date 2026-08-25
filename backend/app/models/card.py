import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class CardApplication(Base):
    __tablename__ = "card_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    card_type = Column(String(20), nullable=False, default="virtual")  # "virtual" or "physical"
    status = Column(String(20), nullable=False, default="pending")  # pending, approved, rejected

    card_number = Column(String(19), nullable=True)  # set on approval only
    expiry_month = Column(Integer, nullable=True)
    expiry_year = Column(Integer, nullable=True)
    cvv = Column(String(4), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="card_applications")