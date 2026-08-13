from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.transaction import TransactionType


class AdminUserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    account_number: str
    balance: Decimal
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminTransactionResponse(BaseModel):
    id: int
    transaction_type: TransactionType
    amount: Decimal
    timestamp: datetime
    sender_id: Optional[int]
    sender_account_number: Optional[str] = None
    receiver_id: Optional[int]
    receiver_account_number: Optional[str] = None
    description: Optional[str]
    status: str

    model_config = ConfigDict(from_attributes=True)