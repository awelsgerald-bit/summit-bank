import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import httpx
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.strowallet_account import StroWalletAccount
from app.models.user import User

logger = logging.getLogger("summit_bank.strowallet")

# Endpoints taken from StroWallet's docs. Only "sterling" has been proven end to end in sandbox
# (HTTP POST with a JSON body). "fidelity" is listed but untested. Nombank (".../amucha", the
# default when no bank is chosen) is deliberately NOT offered.
PROVIDER_PATHS = {
    "sterling": "/virtual-bank/sterling",
    "fidelity": "/virtual-bank/fidelitybank",
}

REQUEST_TIMEOUT_SECONDS = 20.0
# A "pending" row older than this is assumed to belong to a request that died (server restart,
# crash) and may be retried. Shorter than the HTTP timeout would risk two live attempts.
PENDING_STALE_AFTER = timedelta(minutes=2)
NUBAN_RE = re.compile(r"\d{10}")
LOCAL_PHONE_RE = re.compile(r"0\d{10}")


# --------------------------------------------------------------------------------------
# Pure helpers (no database, no network)
# --------------------------------------------------------------------------------------

def normalize_phone(raw: str | None) -> str | None:
    """
    Returns the 11-digit local Nigerian format (08012345678) - the format StroWallet accepted
    in sandbox - or None if the input is not a recognisable Nigerian mobile number.
    """
    if not raw:
        return None
    s = re.sub(r"[\s\-()]", "", raw)
    if s.startswith("+234"):
        s = "0" + s[4:]
    elif s.startswith("234") and len(s) == 13:
        s = "0" + s[3:]
    return s if LOCAL_PHONE_RE.fullmatch(s) else None


def extract_error_text(data, raw_text: str | None, limit: int = 200) -> str:
    """
    StroWallet reports errors two ways: {"message": "text"} and
    {"success": false, "message": {"field": ["error", ...]}}. Flattens both to one short line.
    """
    message = data.get("message") if isinstance(data, dict) else None
    if isinstance(message, dict):
        parts = []
        for field, errors in message.items():
            if isinstance(errors, (list, tuple)):
                errors = "; ".join(str(e) for e in errors)
            parts.append(f"{field}: {errors}")
        text = " | ".join(parts)
    elif isinstance(message, str) and message.strip():
        text = message
    else:
        text = raw_text or ""
    return " ".join(text.split())[:limit]


def _load_config() -> dict:
    """
    Validates configuration at the moment it is used, not at boot, so a typo in an env var
    disables this feature instead of taking the whole API down.
    """
    mode = (settings.strowallet_mode or "").strip().lower()
    provider = (settings.strowallet_provider or "").strip().lower()
    public_key = (settings.strowallet_public_key or "").strip()
    secret = (settings.strowallet_webhook_secret or "").strip()
    backend_url = (settings.backend_base_url or "").strip().rstrip("/")

    problem = None
    if mode not in ("sandbox", "live"):
        problem = "STROWALLET_MODE must be 'sandbox' or 'live'"
    elif mode == "live" and not settings.strowallet_live_enabled:
        problem = "STROWALLET_MODE=live also requires STROWALLET_LIVE_ENABLED=true"
    elif provider not in PROVIDER_PATHS:
        problem = f"STROWALLET_PROVIDER must be one of {sorted(PROVIDER_PATHS)}"
    elif not public_key:
        problem = "STROWALLET_PUBLIC_KEY is not set"
    elif len(secret) < 16:
        problem = "STROWALLET_WEBHOOK_SECRET must be set (at least 16 characters)"
    elif not backend_url.startswith("https://"):
        problem = "BACKEND_BASE_URL must start with https://"

    if problem:
        logger.error("StroWallet is misconfigured: %s", problem)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bank account service is temporarily unavailable.",
        )
    if provider != "sterling":
        logger.warning("StroWallet provider %r has not been tested end to end", provider)

    return {
        "mode": mode,
        "provider": provider,
        "public_key": public_key,
        "url": f"{settings.strowallet_base_url.rstrip('/')}{PROVIDER_PATHS[provider]}",
        "webhook_url": f"{backend_url}/strowallet/webhook?token={quote(secret, safe='')}",
    }


def _is_stale(account: StroWalletAccount) -> bool:
    created = account.created_at
    if created is None:
        return True
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - created > PENDING_STALE_AFTER


# --------------------------------------------------------------------------------------
# Database access
# --------------------------------------------------------------------------------------

def get_my_account(db: Session, user: User) -> StroWalletAccount | None:
    return db.query(StroWalletAccount).filter(StroWalletAccount.user_id == user.id).first()


def _lock_account(db: Session, user: User) -> StroWalletAccount | None:
    """Same lookup, but row-locked so two simultaneous 'apply' requests cannot both retry."""
    return (
        db.query(StroWalletAccount)
        .filter(StroWalletAccount.user_id == user.id)
        .with_for_update()
        .first()
    )


def _fail(db: Session, account: StroWalletAccount, reason: str, http_status: int, detail: str):
    """Records the failure on the row (truncated to the column size) and raises to the caller."""
    account.status = "failed"
    account.failure_reason = reason[:255]
    db.commit()
    raise HTTPException(status_code=http_status, detail=detail)


# --------------------------------------------------------------------------------------
# Main flow
# --------------------------------------------------------------------------------------

def apply_for_account(db: Session, user: User, phone: str | None = None) -> StroWalletAccount:
    cfg = _load_config()

    # Validate everything we can BEFORE touching the database or StroWallet.
    normalized_phone = normalize_phone(phone or user.phone_number)
    if not normalized_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add a valid Nigerian phone number (for example 08012345678) to continue.",
        )
    account_name = " ".join((user.full_name or "").split())
    if not account_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your profile needs a full name first.")

    existing = _lock_account(db, user)
    if existing is not None:
        in_progress = existing.status == "pending" and not _is_stale(existing)
        if existing.status in ("active", "suspended") or in_progress:
            db.rollback()  # release the row lock
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"You already have a StroWallet account application ({existing.status}).",
            )
        # A failed (or abandoned) attempt: reuse the same row instead of deleting it, so its
        # history and any foreign keys pointing at it survive.
        account = existing
        account.status = "pending"
        account.nuban_account_number = None
        account.bank_name = None
        account.account_name = None
        account.activated_at = None
        account.failure_reason = None
        account.created_at = datetime.now(timezone.utc)
    else:
        account = StroWalletAccount(user_id=user.id, status="pending")
        db.add(account)

    account.provider = cfg["provider"]
    account.mode = cfg["mode"]
    if user.phone_number != normalized_phone:
        user.phone_number = normalized_phone

    try:
        db.commit()  # the 'pending' row is now visible to other requests; the call can take seconds
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An application is already in progress.",
        )

    # Same fields and JSON body that worked in the Postman sandbox test.
    body = {
        "public_key": cfg["public_key"],
        "email": user.email,
        "account_name": account_name,
        "phone": normalized_phone,
        "webhook_url": cfg["webhook_url"],
        "mode": cfg["mode"],
    }

    try:
        response = httpx.post(
            cfg["url"],
            json=body,
            headers={"accept": "application/json"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except httpx.TimeoutException:
        logger.error("StroWallet create-account timed out user_id=%s", user.id)
        _fail(
            db, account,
            "StroWallet did not respond in time. Outcome unknown - an account may have been created.",
            status.HTTP_502_BAD_GATEWAY,
            "StroWallet is taking too long to respond. Please try again in a few minutes.",
        )
    except httpx.HTTPError as e:
        logger.error("StroWallet create-account network error user_id=%s: %s", user.id, type(e).__name__)
        _fail(
            db, account,
            f"Network error contacting StroWallet ({type(e).__name__}).",
            status.HTTP_502_BAD_GATEWAY,
            "Could not reach StroWallet right now. Please try again shortly.",
        )

    try:
        data = response.json()
    except ValueError:
        data = None
    if not isinstance(data, dict):
        data = {}

    error_text = extract_error_text(data, response.text)
    success = response.is_success and data.get("success") is True

    if not success:
        # An explicit rejection (non-2xx, or "success": false) carries StroWallet's own reason.
        # Anything else is a response we do not understand: say so, and keep the raw text.
        explicit_rejection = (not response.is_success) or data.get("success") is False
        logger.warning(
            "StroWallet create-account not accepted user_id=%s http=%s explicit=%s detail=%s",
            user.id, response.status_code, explicit_rejection, error_text,
        )
        # StroWallet's validation text (bad phone, rejected name, ...) helps the user for client
        # errors. Server errors and unrecognised responses get a generic message.
        if explicit_rejection and response.status_code < 500 and error_text:
            detail = f"StroWallet could not create the account: {error_text}"
        else:
            detail = "StroWallet could not create the account. Please try again shortly."
        if explicit_rejection:
            reason = f"StroWallet returned HTTP {response.status_code}: {error_text}"
        else:
            reason = f"Unrecognised StroWallet response (HTTP {response.status_code}). Raw: {response.text[:150]}"
        _fail(db, account, reason, status.HTTP_502_BAD_GATEWAY, detail)

    account_number = str(data.get("account_number") or "").strip()
    if not NUBAN_RE.fullmatch(account_number):
        logger.error("StroWallet reported success but no usable account number user_id=%s", user.id)
        _fail(
            db, account,
            f"StroWallet reported success without a valid 10-digit account number. Raw: {response.text[:150]}",
            status.HTTP_502_BAD_GATEWAY,
            "StroWallet returned an unexpected response. Please contact support.",
        )

    account.nuban_account_number = account_number
    account.bank_name = (data.get("bank_name") or None)
    account.account_name = data.get("account_name") or account_name
    account.status = "active"
    account.failure_reason = None
    account.activated_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except IntegrityError:
        # The unique index refused this number: another row already owns it. Crediting by
        # account number would then be ambiguous, so fail closed and keep a clear trail.
        db.rollback()
        logger.error(
            "StroWallet returned account number %s that is already assigned (user_id=%s)",
            account_number, user.id,
        )
        account = get_my_account(db, user)
        account.nuban_account_number = None  # never leave the clashing number on this row
        _fail(
            db, account,
            f"StroWallet returned account number {account_number}, which is already assigned.",
            status.HTTP_502_BAD_GATEWAY,
            "StroWallet returned an unexpected response. Please contact support.",
        )

    db.refresh(account)
    return account