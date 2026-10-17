import json
import logging
import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from typing import NamedTuple

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.strowallet_account import StroWalletAccount
from app.models.strowallet_webhook_event import StroWalletWebhookEvent

# Step 4 stores what StroWallet sent and nothing else. This module deliberately imports no
# transaction, ledger or user-balance code: receiving a webhook can never move money.

logger = logging.getLogger("summit_bank.strowallet")

MAX_BODY_BYTES = 64 * 1024

_ACCOUNT_NUMBER_RE = re.compile(r"[0-9]{1,20}")
_AMOUNT_RE = re.compile(r"[0-9]{1,12}(\.[0-9]+)?")
_TWO_PLACES = Decimal("0.01")
_FLOAT_NOISE = Decimal("0.000001")  # 99.10000000000001 is float noise; 100.005 is not
_MAX_AMOUNT = Decimal("999999999999.99")  # fits Numeric(14, 2)


class RecordResult(NamedTuple):
    outcome: str  # "stored" (new event) or "duplicate" (same sessionId delivered again)
    event_id: int | None
    status: str


# --------------------------------------------------------------------------------------
# Parsing (pure: no database, no network)
# --------------------------------------------------------------------------------------

def parse_amount(value) -> Decimal | None:
    """
    An exact, positive naira amount with at most 2 decimal places, or None. Accepts "100",
    100, "99.1", 99.1. Rejects booleans, NaN/Infinity, exponents, signs, zero, negatives,
    sub-kobo amounts such as 100.005, and anything too large for the database column.
    Tiny float noise (99.10000000000001) is rounded away; real money is never rounded.
    """
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        return None
    text = value.strip() if isinstance(value, str) else str(value)
    if not _AMOUNT_RE.fullmatch(text):
        return None
    exact = Decimal(text)
    rounded = exact.quantize(_TWO_PLACES, rounding=ROUND_HALF_EVEN)
    if abs(rounded - exact) > _FLOAT_NOISE:
        return None
    if rounded <= 0 or rounded > _MAX_AMOUNT:
        return None
    return rounded


def _clean_session_id(value) -> str | None:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    text = str(value).strip()
    if not text or len(text) > 100 or not text.isprintable() or any(ch.isspace() for ch in text):
        return None
    return text


def _clean_account_number(value) -> str | None:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    text = str(value).strip()
    return text if _ACCOUNT_NUMBER_RE.fullmatch(text) else None


def parse_event(raw_text: str) -> dict:
    """
    Pulls the few fields we index out of the payload (camelCase, as in StroWallet's docs).
    Never raises. Anything unexpected becomes status "invalid" with a short reason; the raw
    body is stored either way, so nothing StroWallet sends is ever lost.
    """
    result = {
        "session_id": None,
        "account_number": None,
        "transaction_amount": None,
        "settled_amount": None,
        "status": "received",
        "detail": None,
    }

    try:
        data = json.loads(raw_text, parse_float=Decimal)
    except (ValueError, RecursionError):  # JSONDecodeError is a ValueError; deep nesting is RecursionError
        result.update(status="invalid", detail="Body is not valid JSON")
        return result
    if not isinstance(data, dict):
        result.update(status="invalid", detail="Body is not a JSON object")
        return result

    result["session_id"] = _clean_session_id(data.get("sessionId"))
    result["account_number"] = _clean_account_number(data.get("accountNumber"))
    result["transaction_amount"] = parse_amount(data.get("transactionAmount"))
    result["settled_amount"] = parse_amount(data.get("settledAmount"))

    problems = [
        name
        for name, key in (
            ("sessionId", "session_id"),
            ("accountNumber", "account_number"),
            ("transactionAmount", "transaction_amount"),
            ("settledAmount", "settled_amount"),
        )
        if result[key] is None
    ]
    detail = None
    if problems:
        detail = "Missing or invalid: " + ", ".join(problems)
    elif result["settled_amount"] > result["transaction_amount"]:
        detail = "settledAmount is larger than transactionAmount"
    if detail:
        result.update(status="invalid", detail=detail)
    return result


# --------------------------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------------------------

def record_event(db: Session, raw: bytes) -> RecordResult:
    """
    Saves one inbound notification. The unique index on session_id decides whether this is a
    new event or a repeat delivery, so concurrent deliveries cannot produce two rows. Raises
    on any other database problem: an event we failed to store must not be acknowledged.
    """
    # Text columns cannot hold NUL bytes on Postgres, and invalid UTF-8 must not crash us.
    raw_text = raw.decode("utf-8", errors="replace").replace("\x00", chr(0xFFFD))
    parsed = parse_event(raw_text)

    account = None
    if parsed["status"] == "received":
        account = (
            db.query(StroWalletAccount)
            .filter(StroWalletAccount.nuban_account_number == parsed["account_number"])
            .first()
        )
        if account is None:
            parsed.update(status="unmatched", detail="No Summit account has this account number")
        elif account.status != "active":
            parsed.update(status="unmatched", detail=f"Matching account is {account.status}")

    event = StroWalletWebhookEvent(
        raw_body=raw_text,
        session_id=parsed["session_id"],
        account_number=parsed["account_number"],
        transaction_amount=parsed["transaction_amount"],
        settled_amount=parsed["settled_amount"],
        status=parsed["status"],
        status_detail=parsed["detail"][:255] if parsed["detail"] else None,
        strowallet_account_id=account.id if account is not None else None,
    )
    db.add(event)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        session_id = parsed["session_id"]
        if session_id is None:
            raise  # a row with no sessionId cannot be a duplicate, so something else is wrong
        existing = (
            db.query(StroWalletWebhookEvent)
            .filter(StroWalletWebhookEvent.session_id == session_id)
            .first()
        )
        if existing is None:
            raise
        # Repeat delivery. The first copy stays authoritative; we only count the repeat.
        if existing.raw_body != raw_text:
            logger.warning("StroWallet repeat delivery with a different payload session_id=%s", session_id)
        existing_id = existing.id
        existing_status = existing.status
        (
            db.query(StroWalletWebhookEvent)
            .filter(StroWalletWebhookEvent.id == existing_id)
            .update(
                {
                    StroWalletWebhookEvent.delivery_count: StroWalletWebhookEvent.delivery_count + 1,
                    StroWalletWebhookEvent.last_received_at: datetime.now(timezone.utc),
                },
                synchronize_session=False,
            )
        )
        db.commit()
        return RecordResult("duplicate", existing_id, existing_status)

    return RecordResult("stored", event.id, parsed["status"])