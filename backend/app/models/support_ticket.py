from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String(20), nullable=False, default="general")
    subject = Column(String(120), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="open")  # open, answered, closed
    admin_reply = Column(Text, nullable=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
