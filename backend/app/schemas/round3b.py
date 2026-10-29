from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ScheduleCreate(BaseModel):
    recipient_account_number: str = Field(min_length=1, max_length=20)
    amount: Decimal = Field(gt=0, decimal_places=2, max_digits=14)
    description: Optional[str] = Field(default=None, max_length=255)
    frequency: str = Field(min_length=1, max_length=10)  # once, daily, weekly, monthly
    first_run_at: datetime  # no timezone means Nigerian time
    end_at: Optional[datetime] = None


class ScheduleResponse(BaseModel):
    id: int
    recipient_account_number: str
    recipient_name: str = ""
    amount: Decimal
    description: Optional[str] = None
    frequency: str
    next_run_at: datetime
    end_at: Optional[datetime] = None
    status: str
    run_count: int
    last_run_at: Optional[datetime] = None
    last_status: Optional[str] = None
    last_error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RunResponse(BaseModel):
    id: int
    due_at: datetime
    outcome: str
    transaction_id: Optional[int] = None
    detail: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReferralItem(BaseModel):
    name: str
    joined_at: Optional[datetime] = None
    state: str  # waiting, pending, approved, rejected, none


class ReferralSummary(BaseModel):
    code: str
    bonus_amount: Decimal
    min_first_deposit: Decimal
    invited_count: int
    earned: Decimal
    items: list[ReferralItem]
