import csv
import io
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.transaction import Transaction, TransactionType
from app.models.user import User

# Read-only: statements and receipts never create or change a transaction.

WAT = timezone(timedelta(hours=1))  # Nigeria has no daylight saving
MAX_RANGE_DAYS = 3 * 366
MAX_ROWS = 5000


def day_bounds(start: Optional[date], end: Optional[date]):
    """Turns a date range (Nigerian dates, inclusive) into UTC datetimes [from, to)."""
    if start and end and start > end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start date is after end date")
    if start and end and (end - start).days > MAX_RANGE_DAYS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose a range of three years or less")
    lower = datetime.combine(start, time.min, tzinfo=WAT).astimezone(timezone.utc) if start else None
    upper = datetime.combine(end + timedelta(days=1), time.min, tzinfo=WAT).astimezone(timezone.utc) if end else None
    return lower, upper


def direction_for(tx: Transaction, user_id: int) -> str:
    if tx.transaction_type == TransactionType.DEPOSIT:
        return "credit"
    if tx.transaction_type == TransactionType.WITHDRAWAL:
        return "debit"
    return "debit" if tx.sender_id == user_id else "credit"


def counterparty_name(tx: Transaction, user_id: int) -> str:
    if tx.transaction_type == TransactionType.TRANSFER:
        other = tx.receiver if tx.sender_id == user_id else tx.sender
        return other.full_name if other else "—"
    return "—"


def _local(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(WAT)


def build_statement(db: Session, user: User, start: Optional[date], end: Optional[date]) -> dict:
    lower, upper = day_bounds(start, end)
    query = (
        db.query(Transaction)
        .options(joinedload(Transaction.sender), joinedload(Transaction.receiver))
        .filter(or_(Transaction.sender_id == user.id, Transaction.receiver_id == user.id))
    )
    if lower is not None:
        query = query.filter(Transaction.timestamp >= lower)
    if upper is not None:
        query = query.filter(Transaction.timestamp < upper)
    rows = query.order_by(Transaction.timestamp.desc(), Transaction.id.desc()).limit(MAX_ROWS + 1).all()
    truncated = len(rows) > MAX_ROWS
    rows = rows[:MAX_ROWS]

    items = []
    total_in = Decimal("0")
    total_out = Decimal("0")
    for tx in rows:
        direction = direction_for(tx, user.id)
        # Only approved transactions have actually moved money.
        if tx.status == "approved":
            if direction == "credit":
                total_in += tx.amount
            else:
                total_out += tx.amount
        items.append({
            "id": tx.id,
            "reference": f"SB-{tx.id:08d}",
            "timestamp": tx.timestamp,
            "type": tx.transaction_type.value,
            "direction": direction,
            "amount": tx.amount,
            "currency": tx.currency or "NGN",
            "status": tx.status,
            "description": tx.description or "",
            "counterparty": counterparty_name(tx, user.id),
        })
    return {
        "start": start,
        "end": end,
        "count": len(items),
        "truncated": truncated,
        "total_in": total_in,
        "total_out": total_out,
        "items": items,
    }


def _csv_safe(value: str) -> str:
    """Stops spreadsheet programs from running text that starts like a formula."""
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def statement_csv(user: User, statement: dict) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Summit Bank statement"])
    writer.writerow(["Account name", _csv_safe(user.full_name)])
    writer.writerow(["Account number", user.account_number])
    writer.writerow(["Period", f"{statement['start'] or 'beginning'} to {statement['end'] or 'today'}"])
    writer.writerow(["Total credits (approved)", f"{statement['total_in']:.2f}"])
    writer.writerow(["Total debits (approved)", f"{statement['total_out']:.2f}"])
    writer.writerow([])
    writer.writerow(["Date (WAT)", "Reference", "Type", "Credit/Debit", "Amount", "Currency", "Status", "Counterparty", "Description"])
    for item in statement["items"]:
        writer.writerow([
            _local(item["timestamp"]).strftime("%Y-%m-%d %H:%M"),
            item["reference"],
            item["type"],
            item["direction"],
            f"{item['amount']:f}",
            item["currency"],
            item["status"],
            _csv_safe(item["counterparty"]),
            _csv_safe(item["description"]),
        ])
    return out.getvalue()


def _mask(number: str) -> str:
    return "******" + number[-4:] if number and len(number) > 4 else (number or "—")


def build_receipt(db: Session, user: User, transaction_id: int) -> dict:
    tx = (
        db.query(Transaction)
        .options(joinedload(Transaction.sender), joinedload(Transaction.receiver))
        .filter(Transaction.id == transaction_id)
        .first()
    )
    # A transaction that is not the caller's looks exactly like one that does not exist.
    if tx is None or user.id not in (tx.sender_id, tx.receiver_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    direction = direction_for(tx, user.id)
    is_sender = tx.sender_id == user.id
    if tx.transaction_type == TransactionType.TRANSFER:
        other = tx.receiver if is_sender else tx.sender
        other_number = other.account_number if other else ""
        other_party = {
            "name": other.full_name if other else "—",
            # The sender knows the number they typed; a receiver sees only the last digits.
            "account_number": other_number if is_sender else _mask(other_number),
        }
    else:
        other_party = None
    return {
        "reference": f"SB-{tx.id:08d}",
        "transaction_id": tx.id,
        "type": tx.transaction_type.value,
        "direction": direction,
        "amount": tx.amount,
        "currency": tx.currency or "NGN",
        "status": tx.status,
        "timestamp": tx.timestamp,
        "description": tx.description or "",
        "account_holder": {"name": user.full_name, "account_number": user.account_number},
        "other_party": other_party,
    }
