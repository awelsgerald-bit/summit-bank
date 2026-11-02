from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base


class WebAuthnCredential(Base):
    """A fingerprint / Face ID login registered on one device. Only the PUBLIC key is stored; the
    private key never leaves the phone's secure hardware."""

    __tablename__ = "webauthn_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    credential_id = Column(String(512), unique=True, index=True, nullable=False)  # base64url
    public_key = Column(Text, nullable=False)  # base64url of the DER SubjectPublicKeyInfo
    algorithm = Column(Integer, nullable=False)  # COSE: -7 = ES256, -257 = RS256
    sign_count = Column(Integer, nullable=False, default=0)
    rp_id = Column(String(255), nullable=False)  # the website address it was made for
    label = Column(String(60), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime(timezone=True), nullable=True)
