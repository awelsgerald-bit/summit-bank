from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey

from app.database import Base


class StroWalletWebhookEvent(Base):
    """
    One row per inbound StroWallet transfer notification, saved BEFORE anything is
    parsed, trusted or credited. session_id is unique, so a retried delivery can never
    become a second row (and therefore never a second deposit).
    """

    __tablename__ = "strowallet_webhook_events"

    id = Column(Integer, primary_key=True, index=True)

    # Exactly what StroWallet sent, untouched.
    raw_body = Column(Text, nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_received_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    delivery_count = Column(Integer, nullable=False, default=1, server_default="1")

    # Pulled out of the payload for lookup. session_id is NULL when the body is unparseable
    # (several NULLs are allowed by the unique index); otherwise it is unique per transfer.
    session_id = Column(String(100), nullable=True, unique=True, index=True)
    account_number = Column(String(20), nullable=True, index=True)
    transaction_amount = Column(Numeric(14, 2), nullable=True)  # gross, as sent
    settled_amount = Column(Numeric(14, 2), nullable=True)      # net of fees

    # received -> (invalid | unmatched | unverified | verified | rejected) -> deposit_created
    status = Column(String(20), nullable=False, default="received", server_default="received")
    status_detail = Column(String(255), nullable=True)  # keep short: always truncate before writing

    strowallet_account_id = Column(Integer, ForeignKey("strowallet_accounts.id"), nullable=True, index=True)

    # Verification audit trail (Step 5).
    verify_attempts = Column(Integer, nullable=False, default=0, server_default="0")
    verify_response = Column(Text, nullable=True)  # raw body of StroWallet's verify reply
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Set when the pending deposit is created (Step 6). Unique: one event can only ever
    # produce one transaction.
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True, unique=True)