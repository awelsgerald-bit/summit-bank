from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class QrPaymentRequest(Base):
    """A dynamic QR code: someone asks to be paid, optionally a fixed amount and a reference.
    It can be paid once, before it expires."""

    __tablename__ = "qr_payment_requests"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(24), unique=True, index=True, nullable=False)  # random, goes in the QR
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # who gets paid
    amount = Column(Numeric(14, 2), nullable=True)  # None = the payer chooses
    reference = Column(String(60), nullable=True)
    note = Column(String(140), nullable=True)
    status = Column(String(12), nullable=False, default="open")  # open, paid, cancelled
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User")


class QrTransfer(Base):
    """Links an ordinary Transaction to the QR payment that made it. The unique (sender, key) pair
    is what makes a repeated request with the same Idempotency-Key a no-op."""

    __tablename__ = "qr_transfers"
    __table_args__ = (UniqueConstraint("sender_id", "idempotency_key", name="uq_qr_transfer_idempotency"),)

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(24), unique=True, index=True, nullable=False)  # "SBQ-..." shown on the receipt
    transaction_id = Column(Integer, ForeignKey("transactions.id"), unique=True, nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    payment_request_id = Column(Integer, ForeignKey("qr_payment_requests.id"), nullable=True, unique=True)
    idempotency_key = Column(String(64), nullable=False)
    request_fingerprint = Column(String(64), nullable=False)  # same key with different details is refused
    narration = Column(String(140), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    transaction = relationship("Transaction")
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
