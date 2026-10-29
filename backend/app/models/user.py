from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    beneficiaries = relationship("Beneficiary", back_populates="user")
    account_number = Column(String(20), unique=True, index=True, nullable=False)
    balance = Column(Numeric(14, 2), nullable=False, default=0)
    role = Column(String(20), nullable=False, default="user")  # "user" or "admin"
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    loans = relationship("Loan", back_populates="user")  
    wallets = relationship("Wallet", back_populates="user")
    fixed_deposits = relationship("FixedDeposit", back_populates="user")
    card_applications = relationship("CardApplication", back_populates="user")
    kyc_status = Column(String(20), nullable=False, default="unverified")
    kyc_submissions = relationship("KYCSubmission", back_populates="user")
    wallet_applications = relationship("WalletApplication", back_populates="user")
    strowallet_account = relationship("StroWalletAccount", back_populates="user", uselist=False)
    phone_number = Column(String(20), nullable=True)
    transaction_pin_hash = Column(String(255), nullable=True)  # bcrypt hash of the 4-6 digit PIN
    pin_failed_attempts = Column(Integer, nullable=False, default=0, server_default="0")
    pin_locked_until = Column(DateTime(timezone=True), nullable=True)
    referral_code = Column(String(12), unique=True, index=True, nullable=True)  # made on first use
    referred_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    avatar = Column(Text, nullable=True)  # small profile picture as a data URL (<= 200 KB)
    
    sent_transactions = relationship(
        "Transaction", foreign_keys="Transaction.sender_id", back_populates="sender"
    )
    received_transactions = relationship(
        "Transaction", foreign_keys="Transaction.receiver_id", back_populates="receiver"
    )

    @property
    def has_pin(self) -> bool:
        return self.transaction_pin_hash is not None
