from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LookupResponse(BaseModel):
    account_number: str
    name: str
    is_self: bool


class SavedPaymentCreate(BaseModel):
    label: str = Field(min_length=1, max_length=60)
    recipient_account_number: str = Field(min_length=1, max_length=20)
    amount: Decimal = Field(gt=0, decimal_places=2)
    description: Optional[str] = Field(default=None, max_length=255)


class SavedPaymentResponse(BaseModel):
    id: int
    label: str
    recipient_account_number: str
    recipient_name: str = ""
    amount: Decimal
    description: Optional[str] = None
    last_paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TicketCreate(BaseModel):
    category: str = Field(default="general", max_length=20)
    subject: str = Field(min_length=3, max_length=120)
    message: str = Field(min_length=5, max_length=2000)


class TicketResponse(BaseModel):
    id: int
    category: str
    subject: str
    message: str
    status: str
    admin_reply: Optional[str] = None
    replied_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AdminTicketResponse(TicketResponse):
    user_name: str
    user_email: str


class TicketReply(BaseModel):
    reply: str = Field(min_length=1, max_length=2000)
