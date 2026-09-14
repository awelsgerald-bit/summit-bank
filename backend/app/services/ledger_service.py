import uuid
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ledger import LedgerAccount, LedgerEntry
from app.models.user import User


def get_or_create_user_account(db: Session, user_id: int, currency: str) -> LedgerAccount:
    account = (
        db.query(LedgerAccount)
        .filter(LedgerAccount.user_id == user_id, LedgerAccount.currency == currency, LedgerAccount.account_type == "user_wallet")
        .first()
    )
    if account:
        return account

    account = LedgerAccount(user_id=user_id, currency=currency, account_type="user_wallet")
    db.add(account)
    db.flush()  # get its id without committing yet — caller controls the transaction boundary
    return account


def get_or_create_system_account(db: Session, currency: str, account_type: str) -> LedgerAccount:
    account = (
        db.query(LedgerAccount)
        .filter(LedgerAccount.user_id.is_(None), LedgerAccount.currency == currency, LedgerAccount.account_type == account_type)
        .first()
    )
    if account:
        return account

    account = LedgerAccount(user_id=None, currency=currency, account_type=account_type)
    db.add(account)
    db.flush()
    return account


def already_recorded(db: Session, reference_transaction_id: int, transaction_type: str) -> bool:
    """Idempotency check — has this transaction already been posted to the ledger?"""
    existing = (
        db.query(LedgerEntry)
        .filter(
            LedgerEntry.reference_transaction_id == reference_transaction_id,
            LedgerEntry.transaction_type == transaction_type,
        )
        .first()
    )
    return existing is not None


def record_deposit(
    db: Session,
    user_id: int,
    amount: Decimal,
    currency: str,
    reference_transaction_id: int,
    external_reference: str | None = None,
) -> str:
    """
    Records a deposit as a balanced debit/credit pair:
    - credit to the user's ledger account (money in)
    - debit to the platform clearing account (represents money entering the closed
      ledger system from outside — a real bank transfer, a card payment, etc.)

    Idempotent: calling this twice for the same reference_transaction_id is a no-op
    on the second call.
    """
    if already_recorded(db, reference_transaction_id, "deposit"):
        return "already_recorded"

    entry_group_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    user_account = get_or_create_user_account(db, user_id, currency)
    clearing_account = get_or_create_system_account(db, currency, "platform_clearing")

    db.add(LedgerEntry(
        entry_group_id=entry_group_id,
        ledger_account_id=user_account.id,
        direction="credit",
        amount=amount,
        currency=currency,
        transaction_type="deposit",
        reference_transaction_id=reference_transaction_id,
        external_reference=external_reference,
        status="posted",
        posted_at=now,
    ))
    db.add(LedgerEntry(
        entry_group_id=entry_group_id,
        ledger_account_id=clearing_account.id,
        direction="debit",
        amount=amount,
        currency=currency,
        transaction_type="deposit",
        reference_transaction_id=reference_transaction_id,
        external_reference=external_reference,
        status="posted",
        posted_at=now,
    ))

    return entry_group_id


def get_ledger_balance(db: Session, user_id: int, currency: str) -> Decimal:
    """Computes balance purely from ledger entries — independent of User.balance/Wallet.balance."""
    account = (
        db.query(LedgerAccount)
        .filter(LedgerAccount.user_id == user_id, LedgerAccount.currency == currency, LedgerAccount.account_type == "user_wallet")
        .first()
    )
    if not account:
        return Decimal("0")

    entries = db.query(LedgerEntry).filter(LedgerEntry.ledger_account_id == account.id, LedgerEntry.status == "posted").all()

    total = Decimal("0")
    for e in entries:
        if e.direction == "credit":
            total += e.amount
        else:
            total -= e.amount
    return total


def reconcile_user(db: Session, user: User) -> dict:
    """
    Compares the ledger-computed balance against the currently-authoritative
    stored balance, for both NGN and BTC. Does not fix anything — just reports.
    """
    from app.models.wallet import Wallet

    results = {}

    ngn_ledger_balance = get_ledger_balance(db, user.id, "NGN")
    results["NGN"] = {
        "stored_balance": float(user.balance),
        "ledger_balance": float(ngn_ledger_balance),
        "matches": abs(float(user.balance) - float(ngn_ledger_balance)) < 0.01,
    }

    btc_wallet = db.query(Wallet).filter(Wallet.user_id == user.id, Wallet.currency == "BTC").first()
    if btc_wallet:
        btc_ledger_balance = get_ledger_balance(db, user.id, "BTC")
        results["BTC"] = {
            "stored_balance": float(btc_wallet.balance),
            "ledger_balance": float(btc_ledger_balance),
            "matches": abs(float(btc_wallet.balance) - float(btc_ledger_balance)) < 0.00000001,
        }

    return results