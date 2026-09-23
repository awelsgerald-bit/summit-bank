import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.strowallet_account import StroWalletAccount
from app.models.user import User

STROWALLET_CREATE_ACCOUNT_URL = f"{settings.strowallet_base_url}/virtual-bank/new-customer/"


def get_my_account(db: Session, user: User) -> StroWalletAccount | None:
    return db.query(StroWalletAccount).filter(StroWalletAccount.user_id == user.id).first()


def apply_for_account(db: Session, user: User) -> StroWalletAccount:
    existing = get_my_account(db, user)
    if existing and existing.status in ("pending", "active"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have a StroWallet account application ({existing.status}).",
        )

    # Wipe a previous failed attempt so the user can cleanly retry
    if existing and existing.status == "failed":
        db.delete(existing)
        db.flush()

    account = StroWalletAccount(user_id=user.id, status="pending")
    db.add(account)
    db.flush()  # get its id before the external call, in case we need to reference it

    webhook_url = f"{settings.backend_base_url}/strowallet/webhook?token={settings.strowallet_webhook_secret}"

    try:
        response = httpx.post(
            STROWALLET_CREATE_ACCOUNT_URL,
            data={
                "public_key": settings.strowallet_public_key,
                "email": user.email,
                "account_name": user.full_name,
                "phone": user.phone_number if hasattr(user, "phone_number") else "N/A",
                "webhook_url": webhook_url,
                "mode": settings.strowallet_mode,  # "sandbox" or "live"
            },
            timeout=20.0,
        )
    except httpx.HTTPError as e:
        account.status = "failed"
        account.failure_reason = f"Network error contacting StroWallet: {e}"
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not reach StroWallet right now.")

        print(f"[StroWallet] Raw response ({response.status_code}): {response.text[:1000]}")

    data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}

    if response.status_code != 200 or not data:
        account.status = "failed"
        account.failure_reason = f"StroWallet returned {response.status_code}: {response.text[:300]}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="StroWallet could not create the account. Please try again shortly.",
        )

    # NOTE: exact field names below are StroWallet's documented response shape as of
    # this integration date — confirm these against your live sandbox response the
    # first time this runs, since third-party API response shapes can drift.
    account.nuban_account_number = data.get("accountNumber")
    account.bank_name = data.get("bankName", "Nombank MFB")
    account.account_name = data.get("accountName", user.full_name)
    account.strowallet_customer_reference = data.get("sessionId") or data.get("customerId")
    account.status = "active" if account.nuban_account_number else "failed"
    if account.status == "failed":
        account.failure_reason = "StroWallet response missing account number"

    db.commit()
    db.refresh(account)
    return account