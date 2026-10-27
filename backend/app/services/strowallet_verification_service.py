import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import NamedTuple, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.strowallet_account import StroWalletAccount
from app.models.strowallet_webhook_event import StroWalletWebhookEvent
from app.services.strowallet_webhook_service import parse_amount

# Step 5 asks StroWallet "did this transfer really happen?" before anything else may trust a
# webhook. It is fail-closed: an event becomes "verified" only when StroWallet answers HTTP 200
# with a body that shows no sign of failure and nothing that contradicts what the webhook said.
# Every other outcome (error, timeout, odd reply, mismatch) leaves the event unverified.
#
# This module imports no transaction, ledger or user-balance code. Verifying an event moves no
# money; creating the pending deposit is Step 6.

logger = logging.getLogger("summit_bank.strowallet")

# httpx logs every request URL at INFO, and our verify URL carries the public key.
logging.getLogger("httpx").setLevel(logging.WARNING)

VERIFY_PATH = "/verifysessionid/"
REQUEST_TIMEOUT_SECONDS = 10
MAX_AUTO_ATTEMPTS = 3          # automatic tries (webhook + repeat deliveries) before "rejected"
MAX_STORED_REPLY_CHARS = 4000

# Which states may (re)enter verification. "verified" and "deposit_created" are final here.
AUTO_STATES = ("received", "unverified")
MANUAL_STATES = ("received", "unverified", "rejected")

_FAIL_STATUS_WORDS = {"false", "failed", "fail", "failure", "error", "pending", "declined", "unsuccessful", "not_found"}
_FAIL_MESSAGE_PARTS = ("not received", "not found", "not exist", "fail", "invalid", "error", "declin", "unsuccessful")
_AMOUNT_KEYS = ("amount", "transactionAmount", "settledAmount", "transaction_amount", "settled_amount")
_SESSION_KEYS = ("sessionId", "sessionID", "session_id")


class VerifyResult(NamedTuple):
    outcome: str  # "verified" | "unverified" | "rejected" | "skipped" | "not_configured" | "not_found"
    status: Optional[str]
    detail: str


# --------------------------------------------------------------------------------------
# Pure decision logic (no database, no network)
# --------------------------------------------------------------------------------------

def interpret_verify_reply(
    http_status: int,
    body_text: str,
    expected_amounts: set,
    session_id: str,
) -> tuple[bool, str]:
    """
    Returns (confirmed, reason). Confirmed only for HTTP 200 + a JSON object that carries no
    failure signal and no contradicting amount or session id. StroWallet's documented failure
    is HTTP 400 {"message": "Transaction not received.", "status": 400}; its confirmed success
    reply is {"message": "Transaction received.", "status": 200}. Only that is accepted; any
    other reply is refused and stored so it can be inspected.
    """
    if http_status != 200:
        return False, f"StroWallet answered HTTP {http_status}"

    try:
        data = json.loads(body_text, parse_float=Decimal)
    except (ValueError, RecursionError):
        return False, "Verify reply was HTTP 200 but not JSON"
    if not isinstance(data, dict):
        return False, "Verify reply was HTTP 200 but not a JSON object"

    layers = [data]
    inner = data.get("data")
    if isinstance(inner, dict):
        layers.append(inner)

    for layer in layers:
        st = layer.get("status")
        if st is False:
            return False, "Verify reply status is false"
        if isinstance(st, (int, Decimal)) and not isinstance(st, bool) and not (200 <= st < 300):
            return False, f"Verify reply status is {st}"
        if isinstance(st, str) and st.strip().lower() in _FAIL_STATUS_WORDS:
            return False, f"Verify reply status is {st.strip()[:40]!r}"

        ok = layer.get("success")
        if ok is False or (isinstance(ok, str) and ok.strip().lower() == "false"):
            return False, "Verify reply says success is false"

        message = layer.get("message")
        if isinstance(message, str) and any(part in message.lower() for part in _FAIL_MESSAGE_PARTS):
            return False, f"Verify reply message looks like a failure: {message[:80]!r}"

        for key in _SESSION_KEYS:
            if key in layer and str(layer[key]).strip() != session_id:
                return False, "Verify reply is about a different sessionId"

        for key in _AMOUNT_KEYS:
            if key in layer:
                value = parse_amount(layer[key])
                if value is None:
                    return False, f"Verify reply has an unreadable {key}"
                if value not in expected_amounts:
                    return False, f"Verify reply {key} does not match the webhook"

    # Positive proof required. StroWallet support confirmed (ticket #1808, 19 Oct 2026) that a
    # valid sessionID returns exactly {"message": "Transaction received.", "status": 200}.
    # Anything else, including an empty object, is refused.
    message = data.get("message")
    status_ok = data.get("status") == 200 and not isinstance(data.get("status"), bool)
    message_ok = isinstance(message, str) and message.strip().rstrip(".").lower() == "transaction received"
    if not (status_ok and message_ok):
        return False, "Verify reply was HTTP 200 but is not StroWallet's 'Transaction received' confirmation"

    return True, "StroWallet confirmed the transfer"


def _scrub(text: str, secrets: list) -> str:
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[redacted]")
    return text[:MAX_STORED_REPLY_CHARS]


def _config() -> Optional[dict]:
    public_key = (settings.strowallet_public_key or "").strip()
    base = (settings.strowallet_base_url or "").strip().rstrip("/")
    basis = (settings.strowallet_verify_amount or "").strip().lower()
    if not public_key or not base.startswith("https://") or basis not in ("transaction", "settled"):
        logger.error("StroWallet verification is misconfigured (public key, base URL or STROWALLET_VERIFY_AMOUNT)")
        return None
    return {"public_key": public_key, "url": f"{base}{VERIFY_PATH}", "basis": basis}


# --------------------------------------------------------------------------------------
# Verification of one stored event
# --------------------------------------------------------------------------------------

def _finish(db: Session, event_id: int, allowed: tuple, **values) -> bool:
    """Writes the outcome only if the event is still in a state that may change. Never moves
    a verified or deposit_created event, however many verifications overlap."""
    changed = (
        db.query(StroWalletWebhookEvent)
        .filter(StroWalletWebhookEvent.id == event_id, StroWalletWebhookEvent.status.in_(allowed))
        .update(values, synchronize_session=False)
    )
    db.commit()
    return bool(changed)


def verify_event(db: Session, event_id: int, manual: bool = False) -> VerifyResult:
    """
    Asks StroWallet to confirm one stored webhook event and records the answer. Never raises
    for StroWallet or network problems: those simply leave the event unverified. Automatic runs
    may try an event MAX_AUTO_ATTEMPTS times; an admin ("manual") can always try again.
    """
    allowed = MANUAL_STATES if manual else AUTO_STATES

    cfg = _config()
    if cfg is None:
        return VerifyResult("not_configured", None, "Verification is not configured")

    event = db.query(StroWalletWebhookEvent).filter(StroWalletWebhookEvent.id == event_id).first()
    if event is None:
        return VerifyResult("not_found", None, "No such event")
    if event.status not in allowed:
        return VerifyResult("skipped", event.status, f"Event is {event.status}; nothing to verify")
    # Copy what we need now: commit() expires the ORM object and a later read would reload it.
    session_id = event.session_id
    transaction_amount = event.transaction_amount
    settled_amount = event.settled_amount
    account_id = event.strowallet_account_id
    attempts_before = event.verify_attempts or 0

    if not manual and attempts_before >= MAX_AUTO_ATTEMPTS:
        return VerifyResult("skipped", event.status, "Automatic attempts used up; an admin can retry")

    # Re-check the account now: it may have been suspended since the webhook arrived.
    account = None
    if account_id is not None:
        account = db.query(StroWalletAccount).filter(StroWalletAccount.id == account_id).first()
    if account is None or account.status != "active":
        detail = "The matching account is no longer active"
        _finish(db, event_id, allowed, status="unmatched", status_detail=detail)
        return VerifyResult("skipped", "unmatched", detail)

    amount = transaction_amount if cfg["basis"] == "transaction" else settled_amount
    expected = {a for a in (transaction_amount, settled_amount) if a is not None}
    if amount is None or session_id is None:
        detail = "Event has no usable amount or sessionId"
        _finish(db, event_id, allowed, status="invalid", status_detail=detail)
        return VerifyResult("skipped", "invalid", detail)

    # Count the attempt before calling out, so a crash mid-call still counts.
    claimed = (
        db.query(StroWalletWebhookEvent)
        .filter(StroWalletWebhookEvent.id == event_id, StroWalletWebhookEvent.status.in_(allowed))
        .update({StroWalletWebhookEvent.verify_attempts: StroWalletWebhookEvent.verify_attempts + 1},
                synchronize_session=False)
    )
    db.commit()
    if not claimed:
        return VerifyResult("skipped", None, "Event changed state; nothing to verify")
    attempts = attempts_before + 1

    reply_text = None
    try:
        response = httpx.get(
            cfg["url"],
            params={
                "public_key": cfg["public_key"],
                "amount": f"{amount:.2f}",
                "sessionID": session_id,
            },
            headers={"accept": "application/json"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        reply_text = response.text
        confirmed, reason = interpret_verify_reply(response.status_code, reply_text, expected, session_id)
        definitive_no = not confirmed
    except httpx.HTTPError as e:
        # Our problem or theirs, but not an answer about the transfer. Log the type only: the
        # exception text can contain the request URL, which holds the public key.
        logger.warning("StroWallet verify call failed event_id=%s error=%s", event_id, type(e).__name__)
        confirmed, definitive_no = False, False
        reason = f"Could not reach StroWallet's verify service ({type(e).__name__})"

    stored_reply = _scrub(reply_text, [cfg["public_key"]]) if reply_text is not None else None

    if confirmed:
        applied = _finish(
            db, event_id, allowed,
            status="verified",
            status_detail=reason[:255],
            verify_response=stored_reply,
            verified_at=datetime.now(timezone.utc),
        )
        logger.info("StroWallet event verified event_id=%s applied=%s", event_id, applied)
        return VerifyResult("verified" if applied else "skipped", "verified" if applied else None, reason)

    final = "rejected" if (definitive_no and attempts >= MAX_AUTO_ATTEMPTS) else "unverified"
    _finish(
        db, event_id, allowed,
        status=final,
        status_detail=reason[:255],
        verify_response=stored_reply,
    )
    logger.info("StroWallet event not verified event_id=%s status=%s attempts=%s", event_id, final, attempts)
    return VerifyResult(final, final, reason)


def verify_event_in_background(event_id: int) -> None:
    """Entry point for FastAPI background tasks: opens its own session (the request's session
    is closed by then) and never lets an exception escape."""
    from app.database import SessionLocal  # imported here so tests need no database engine

    db = None
    try:
        db = SessionLocal()
        verify_event(db, event_id)
    except Exception:
        logger.exception("Background verification crashed event_id=%s", event_id)
        if db is not None:
            try:
                db.rollback()
            except Exception:
                pass
    finally:
        if db is not None:
            db.close()