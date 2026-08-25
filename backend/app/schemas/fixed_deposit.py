from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

TERM_OPTIONS_DAYS = [30, 90, 180, 365]


class FixedDepositCreate(BaseModel):
    principal_amount: Decimal = Field(gt=0)
    term_days: int

    def validate_term(self):
        if self.term_days not in TERM_OPTIONS_DAYS:
            raise ValueError(f"term_days must be one of {TERM_OPTIONS_DAYS}")


class FixedDepositResponse(BaseModel):
    id: int
    principal_amount: Decimal
    interest_rate: Decimal
    term_days: int
    payout_amount: Decimal
    status: str
    created_at: datetime
    matures_at: datetime
    matured_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)