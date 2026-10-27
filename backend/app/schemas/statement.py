from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class StatementItem(BaseModel):
    id: int
    reference: str
    timestamp: datetime
    type: str
    direction: str
    amount: Decimal
    currency: str
    status: str
    description: str
    counterparty: str


class StatementResponse(BaseModel):
    start: Optional[date] = None
    end: Optional[date] = None
    count: int
    truncated: bool
    total_in: Decimal
    total_out: Decimal
    items: list[StatementItem]


class ReceiptParty(BaseModel):
    name: str
    account_number: str


class ReceiptResponse(BaseModel):
    reference: str
    transaction_id: int
    type: str
    direction: str
    amount: Decimal
    currency: str
    status: str
    timestamp: datetime
    description: str
    account_holder: ReceiptParty
    other_party: Optional[ReceiptParty] = None
