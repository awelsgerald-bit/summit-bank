from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class KYCSubmission(Base):
    __tablename__ = "kyc_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    full_legal_name = Column(String(150), nullable=False)
    date_of_birth = Column(String(10), nullable=False)  # stored as "YYYY-MM-DD" string, kept simple
    id_type = Column(String(30), nullable=False)  # "passport", "national_id", "drivers_license"
    id_number = Column(String(50), nullable=False)
    address = Column(Text, nullable=False)

    status = Column(String(20), nullable=False, default="pending")  # pending, approved, rejected
    rejection_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="kyc_submissions")