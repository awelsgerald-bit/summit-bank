from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.transaction import TransactionType


class DepositRequest(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    description: Optional[str] = None


class WithdrawRequest(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    description: Optional[str] = None


class TransferRequest(BaseModel):
    recipient_account_number: str = Field(min_length=1, max_length=20)
    amount: Decimal = Field(gt=0, decimal_places=2)
    description: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    transaction_type: TransactionType
    amount: Decimal
    timestamp: datetime
    sender_id: Optional[int]
    receiver_id: Optional[int]
    description: Optional[str]
    status: str
    model_config = ConfigDict(from_attributes=True)