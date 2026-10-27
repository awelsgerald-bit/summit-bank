from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    target_amount: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2, max_digits=14)


class PotMove(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2, max_digits=14)


class PotResponse(BaseModel):
    id: int
    name: str
    target_amount: Optional[Decimal] = None
    balance: Decimal
    status: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PotActionResponse(BaseModel):
    pot: PotResponse
    wallet_balance: Decimal


class PotListResponse(BaseModel):
    pots: list[PotResponse]
    total_saved: Decimal


class MovementResponse(BaseModel):
    id: int
    kind: str
    amount: Decimal
    pot_balance_after: Decimal
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
