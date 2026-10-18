from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StroWalletApplyRequest(BaseModel):
    # Optional: lets users who registered without a phone number supply one when applying.
    phone: Optional[str] = Field(default=None, max_length=20)


class StroWalletAccountResponse(BaseModel):
    id: int
    nuban_account_number: Optional[str]
    bank_name: Optional[str]
    account_name: Optional[str]
    provider: Optional[str]
    mode: str
    status: str
    created_at: datetime
    activated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class StroWalletEventSummary(BaseModel):
    """Admin list view of an inbound StroWallet notification. Never includes the raw body."""
    id: int
    session_id: Optional[str]
    account_number: Optional[str]
    transaction_amount: Optional[Decimal]
    settled_amount: Optional[Decimal]
    status: str
    status_detail: Optional[str]
    delivery_count: int
    verify_attempts: int
    received_at: datetime
    verified_at: Optional[datetime]
    transaction_id: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class StroWalletEventDetail(StroWalletEventSummary):
    """Admin detail view: adds what StroWallet sent and what its verify service answered."""
    raw_body: str
    verify_response: Optional[str]
    last_received_at: datetime
