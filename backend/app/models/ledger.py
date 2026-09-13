from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class LedgerAccount(Base):
    __tablename__ = "ledger_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "currency", "account_type", name="uq_ledger_account_identity"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL = system account
    currency = Column(String(10), nullable=False)
    account_type = Column(String(30), nullable=False)  # "user_wallet", "platform_clearing", "loan_receivable", etc.
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    entries = relationship("LedgerEntry", back_populates="account")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    entry_group_id = Column(String(64), nullable=False, index=True)
    ledger_account_id = Column(Integer, ForeignKey("ledger_accounts.id"), nullable=False)

    direction = Column(String(10), nullable=False)  # "debit" or "credit"
    amount = Column(Numeric(20, 8), nullable=False)  # always positive; direction determines effect
    currency = Column(String(10), nullable=False)

    transaction_type = Column(String(30), nullable=False)  # "deposit", "withdrawal", etc.
    reference_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    external_reference = Column(String(100), nullable=True)  # StroWallet/Paystack ref, for reconciliation

    status = Column(String(20), nullable=False, default="posted")  # posted, reversed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    posted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    account = relationship("LedgerAccount", back_populates="entries")