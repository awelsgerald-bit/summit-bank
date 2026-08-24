from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class LoanApplicationCreate(BaseModel):
    principal_amount: Decimal = Field(gt=0)
    term_months: int = Field(gt=0, le=60)
    purpose: Optional[str] = None


class LoanResponse(BaseModel):
    id: int
    principal_amount: Decimal
    interest_rate: Decimal
    term_months: int
    purpose: Optional[str]
    total_repayable: Optional[Decimal]
    outstanding_balance: Optional[Decimal]
    status: str
    created_at: datetime
    approved_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class RepaymentRequest(BaseModel):
    amount: Decimal = Field(gt=0)