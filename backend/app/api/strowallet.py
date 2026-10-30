import hmac
import logging
import re
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.strowallet import StroWalletAccountResponse, StroWalletApplyRequest
from app.services import strowallet_deposit_service, strowallet_service, strowallet_webhook_service

logger = logging.getLogger("summit_bank.strowallet")

router = APIRouter(prefix="/strowallet", tags=["StroWallet"])


class _RedactWebhookToken(logging.Filter):
    """
    StroWallet's webhooks are unsigned, so our only protection is a secret token in the URL.
    Uvicorn's access log prints the full URL of every request, which would write that token
    into the logs. This rewrites "token=..." to "token=[redacted]" before a line is emitted.
    """

    tag = "strowallet-webhook-token"
    _pattern = re.compile(r"([?&]token=)[^&\s\"']+")

    def _clean(self, value):
        return self._pattern.sub(r"\1[redacted]", value) if isinstance(value, str) else value

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = self._clean(record.msg)
            if isinstance(record.args, tuple):
                record.args = tuple(self._clean(a) for a in record.args)
        except Exception:  # a logging filter must never break logging
            pass
        return True


_access_logger = logging.getLogger("uvicorn.access")
if not any(getattr(f, "tag", None) == _RedactWebhookToken.tag for f in _access_logger.filters):
    _access_logger.addFilter(_RedactWebhookToken())


def _webhook_token_is_valid(token: str) -> bool:
    secret = (settings.strowallet_webhook_secret or "").strip()
    if len(secret) < 16:
        # Not configured (or too weak to trust): refuse everything rather than compare to "".
        logger.error("STROWALLET_WEBHOOK_SECRET is missing or shorter than 16 characters; rejecting webhooks")
        return False
    return hmac.compare_digest((token or "").encode("utf-8"), secret.encode("utf-8"))


def _caller_ip(request: Request) -> tuple[str, str]:
    """The caller's address as our host sees it, and the raw chain, for logging. The platform adds the
    real caller to the END of X-Forwarded-For, so we count from the right (anything to its left can be forged)."""
    chain = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
    direct = request.client.host if request.client else ""
    hops = max(1, int(settings.strowallet_webhook_ip_hops or 1))
    ip = chain[-hops] if len(chain) >= hops else direct
    return ip, f"xff={','.join(chain) or '-'} direct={direct or '-'}"


def _webhook_ip_allowed(request: Request) -> bool:
    allowed = {p.strip() for p in (settings.strowallet_webhook_ips or "").split(",") if p.strip()}
    ip, detail = _caller_ip(request)
    logger.info("StroWallet webhook caller %s picked=%s", detail, ip)
    return not allowed or ip in allowed


@router.post(
    "/apply",
    response_model=StroWalletAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
def apply_for_account(
    payload: Optional[StroWalletApplyRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    phone = payload.phone if payload else None
    return strowallet_service.apply_for_account(db, current_user, phone)


@router.get(
    "/my-account",
    response_model=StroWalletAccountResponse,
)
def get_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = strowallet_service.get_my_account(db, current_user)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No StroWallet account found. Apply first.",
        )

    return account


@router.post("/webhook")
async def strowallet_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    token: str = "",
    db: Session = Depends(get_db),
):
    # 1. Authenticate before reading anything. A real 401 on any mismatch.
    if not _webhook_token_is_valid(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook token",
        )

    # 1b. Optional second lock: only StroWallet's address may post (set STROWALLET_WEBHOOK_IPS).
    if not _webhook_ip_allowed(request):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Caller not allowed")

    # 2. Refuse absurdly large bodies without buffering them.
    max_bytes = strowallet_webhook_service.MAX_BODY_BYTES
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > max_bytes:
        raise HTTPException(status_code=413, detail="Payload too large")
    raw_body = await request.body()
    if len(raw_body) > max_bytes:
        raise HTTPException(status_code=413, detail="Payload too large")

    # 3. Save what arrived, untouched, before anything else. This step credits nothing and
    #    creates no transaction; a database failure raises (500) so the event is not acknowledged.
    result = await run_in_threadpool(strowallet_webhook_service.record_event, db, raw_body)
    logger.info(
        "StroWallet webhook event_id=%s outcome=%s status=%s",
        result.event_id, result.outcome, result.status,
    )

    # 4. AFTER we have answered: ask StroWallet whether the transfer really happened and, only if it
    #    confirms, create a PENDING deposit for admin approval. This request itself credits nothing.
    #    Only events that matched an active account and parsed cleanly are worth processing; a repeat
    #    delivery of one that is not finished gets another try (a lost background task heals itself).
    if result.event_id is not None and result.status in strowallet_deposit_service.PROCESSABLE_STATES:
        background_tasks.add_task(strowallet_deposit_service.process_event_in_background, result.event_id)

    # The reply never reveals whether the event matched an account or was valid.
    return {"received": True}