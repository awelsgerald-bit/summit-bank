from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class StroWalletAccount(Base):
    __tablename__ = "strowallet_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Inbound webhooks identify the destination only by this number ("accountNumber"),
    # so it must be globally unique. NULL until StroWallet responds.
    nuban_account_number = Column(String(20), nullable=True, unique=True, index=True)
    bank_name = Column(String(100), nullable=True)  # display name as returned by StroWallet
    account_name = Column(String(150), nullable=True)

    # Which StroWallet endpoint created this account: "sterling", "fidelity", ...
    provider = Column(String(30), nullable=True)
    # "sandbox" or "live" - recorded at creation so test accounts can never be mistaken for real ones.
    mode = Column(String(10), nullable=False, default="sandbox", server_default="sandbox")

    # DEPRECATED: StroWallet returns no customer/session id at account creation, so this is
    # always NULL. Kept for now (no destructive changes in Step 2); Step 3 stops writing to it.
    strowallet_customer_reference = Column(String(100), nullable=True, unique=True)

    status = Column(String(20), nullable=False, default="pending")  # pending, active, failed, suspended
    failure_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    activated_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="strowallet_account")