"""Fingerprint / Face ID sign-in using WebAuthn (passkeys).

How it works, in plain words: the phone makes a private key inside its secure hardware, protected
by the fingerprint or face. We store only the matching PUBLIC key. To sign in, we send a one-time
challenge; the phone signs it after a fingerprint/face check; we verify the signature with the
stored public key. Nothing secret ever travels, and a stolen database cannot sign in as anyone.

What is checked on every sign-in (each has a test): the challenge is ours, unexpired and for sign-in;
the request came from our own website; the credential belongs to the address it was made on; the
authenticator confirmed the person (user verification); the signature is valid; and the signature
counter never goes backwards (a cloned key would).

No new libraries: this uses the `cryptography` package that is already installed with python-jose.
"""
import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password
from app.models.user import User
from app.models.webauthn import WebAuthnCredential
from app.services import rate_limit

logger = logging.getLogger("summit_bank.webauthn")

CHALLENGE_TTL_SECONDS = 180
MAX_CREDENTIALS_PER_USER = 5
ES256, RS256 = -7, -257
FLAG_UP, FLAG_UV = 0x01, 0x04


def b64u_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def b64u_decode(text: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))
    except Exception:
        raise _fail(400, "Invalid data from the device.")


def _fail(code: int, message: str) -> HTTPException:
    return HTTPException(status_code=code, detail=message)


def _login_failed() -> HTTPException:
    return _fail(401, "Fingerprint / Face ID sign-in failed. Use your password instead.")


# ------------------------------------------------------------------ challenges (stateless, signed)

def _mac(message: str) -> str:
    return hmac.new(settings.secret_key.encode(), b"webauthn:" + message.encode(), hashlib.sha256).hexdigest()


def make_challenge(purpose: str, user_id: int = 0) -> str:
    body = f"{purpose}:{user_id}:{int(time.time())}:{secrets.token_urlsafe(18)}"
    return b64u_encode(f"{body}.{_mac(body)}".encode())


def check_challenge(challenge: str, purpose: str, user_id: int = 0) -> None:
    try:
        text = b64u_decode(challenge).decode()
        body, mac = text.rsplit(".", 1)
        p, uid, issued, _ = body.split(":", 3)
        ok = hmac.compare_digest(mac, _mac(body)) and p == purpose and int(uid) == user_id
        fresh = 0 <= time.time() - int(issued) <= CHALLENGE_TTL_SECONDS
    except HTTPException:
        raise
    except Exception:
        raise _fail(400, "That request has expired. Please try again.")
    if not ok or not fresh:
        raise _fail(400, "That request has expired. Please try again.")


# ------------------------------------------------------------------ checking what the browser sends

def allowed_origins() -> set[str]:
    origins = {o.rstrip("/") for o in settings.allowed_origins}
    origins.add(settings.frontend_url.rstrip("/"))
    return origins


def _client_data(client_data_b64: str, expected_type: str, purpose: str, user_id: int) -> tuple[bytes, str]:
    raw = b64u_decode(client_data_b64)
    try:
        data = json.loads(raw)
    except ValueError:
        raise _fail(400, "Invalid data from the device.")
    if data.get("type") != expected_type:
        raise _fail(400, "Invalid data from the device.")
    check_challenge(str(data.get("challenge", "")), purpose, user_id)
    origin = str(data.get("origin", "")).rstrip("/")
    if origin not in allowed_origins():
        logger.warning("WebAuthn refused: origin %r is not allowed", origin)
        raise _fail(403, "This website address is not allowed for fingerprint sign-in.")
    return raw, urlparse(origin).hostname or ""


def _load_public_key(public_key_b64: str, algorithm: int):
    try:
        key = serialization.load_der_public_key(b64u_decode(public_key_b64))
    except HTTPException:
        raise
    except Exception:
        raise _fail(400, "Invalid key from the device.")
    if algorithm == ES256 and isinstance(key, ec.EllipticCurvePublicKey) and key.curve.name == "secp256r1":
        return key
    if algorithm == RS256 and isinstance(key, rsa.RSAPublicKey) and key.key_size >= 2048:
        return key
    raise _fail(400, "This device uses a key type that is not supported.")


# ------------------------------------------------------------------ registering (user is signed in)

def begin_registration(db: Session, user: User) -> dict:
    existing = db.query(WebAuthnCredential).filter(WebAuthnCredential.user_id == user.id).all()
    return {
        "challenge": make_challenge("register", user.id),
        "user": {"id": b64u_encode(f"summit-{user.id}".encode()), "name": user.email, "display_name": user.full_name},
        "exclude": [c.credential_id for c in existing],
    }


def finish_registration(db: Session, user: User, password: str, credential_id: str, public_key: str,
                        algorithm: int, client_data_json: str, label: str | None) -> WebAuthnCredential:
    if not verify_password(password or "", user.hashed_password):
        raise _fail(400, "Your account password is incorrect")
    _, rp_id = _client_data(client_data_json, "webauthn.create", "register", user.id)
    _load_public_key(public_key, algorithm)  # refuses anything we cannot verify later
    if len(b64u_decode(credential_id)) < 16:
        raise _fail(400, "Invalid data from the device.")
    count = db.query(WebAuthnCredential).filter(WebAuthnCredential.user_id == user.id).count()
    if count >= MAX_CREDENTIALS_PER_USER:
        raise _fail(400, f"You can register up to {MAX_CREDENTIALS_PER_USER} devices. Remove one first.")
    if db.query(WebAuthnCredential).filter(WebAuthnCredential.credential_id == credential_id).first():
        raise _fail(409, "This device is already registered.")
    cred = WebAuthnCredential(
        user_id=user.id, credential_id=credential_id, public_key=public_key, algorithm=algorithm,
        sign_count=0, rp_id=rp_id, label=(label or "").strip()[:60] or "This device",
    )
    db.add(cred)
    db.commit()
    db.refresh(cred)
    logger.info("Biometric credential %s registered for user %s", cred.id, user.id)
    return cred


def list_credentials(db: Session, user: User) -> list[WebAuthnCredential]:
    return (
        db.query(WebAuthnCredential).filter(WebAuthnCredential.user_id == user.id)
        .order_by(WebAuthnCredential.created_at.desc()).all()
    )


def remove_credential(db: Session, user: User, credential_pk: int) -> None:
    cred = (
        db.query(WebAuthnCredential)
        .filter(WebAuthnCredential.id == credential_pk, WebAuthnCredential.user_id == user.id)  # only your own
        .first()
    )
    if cred is None:
        raise _fail(404, "Device not found.")
    db.delete(cred)
    db.commit()


# ------------------------------------------------------------------ signing in

def finish_login(db: Session, credential_id: str, client_data_json: str, authenticator_data: str,
                 signature: str) -> User:
    if not rate_limit.allow("biometric-login", 60, 60) or not rate_limit.allow(f"biometric:{credential_id[:64]}", 10, 60):
        raise _fail(429, "Too many attempts. Wait a minute and try again.")
    cred = db.query(WebAuthnCredential).filter(WebAuthnCredential.credential_id == credential_id).first()
    if cred is None:
        raise _login_failed()
    try:
        raw_client, host = _client_data(client_data_json, "webauthn.get", "login", 0)
    except HTTPException:
        logger.warning("Biometric login refused for credential %s (client data)", cred.id)
        raise _login_failed()
    if host != cred.rp_id:
        logger.warning("Biometric login refused for credential %s: made for %s, used on %s", cred.id, cred.rp_id, host)
        raise _login_failed()

    auth_data = b64u_decode(authenticator_data)
    if len(auth_data) < 37 or auth_data[:32] != hashlib.sha256(cred.rp_id.encode()).digest():
        raise _login_failed()
    flags = auth_data[32]
    if not (flags & FLAG_UP) or not (flags & FLAG_UV):  # present AND verified by fingerprint/face/PIN
        raise _login_failed()
    counter = int.from_bytes(auth_data[33:37], "big")

    key = _load_public_key(cred.public_key, cred.algorithm)
    signed = auth_data + hashlib.sha256(raw_client).digest()
    try:
        sig = b64u_decode(signature)
        if cred.algorithm == ES256:
            key.verify(sig, signed, ec.ECDSA(hashes.SHA256()))
        else:
            key.verify(sig, signed, padding.PKCS1v15(), hashes.SHA256())
    except InvalidSignature:
        logger.warning("Biometric login refused for credential %s: bad signature", cred.id)
        raise _login_failed()

    if (counter or cred.sign_count) and counter <= cred.sign_count:
        logger.warning("Biometric login refused for credential %s: counter went backwards", cred.id)
        raise _login_failed()

    user = db.query(User).filter(User.id == cred.user_id).first()
    if user is None:
        raise _login_failed()
    cred.sign_count = counter
    cred.last_used_at = datetime.now(timezone.utc)
    db.commit()
    return user
