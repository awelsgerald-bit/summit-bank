from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ResolveRequest(BaseModel):
    payload: str = Field(min_length=1, max_length=200)


class QrTransferRequest(BaseModel):
    payload: str = Field(min_length=1, max_length=200)
    amount: Optional[Decimal] = None  # may be left out only for a request that has a fixed amount
    narration: Optional[str] = Field(default=None, max_length=140)


class PaymentRequestCreate(BaseModel):
    amount: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2)
    reference: Optional[str] = Field(default=None, max_length=60)
    note: Optional[str] = Field(default=None, max_length=140)
    expires_minutes: int = Field(default=60, ge=1, le=7 * 24 * 60)
