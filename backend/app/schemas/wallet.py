from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class WalletResponse(BaseModel):
    id: int
    currency: str
    balance: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WalletApplyRequest(BaseModel):
    currency: str  # "BTC" for now

class WalletApplicationCreate(BaseModel):
    currency: str
    reason: Optional[str] = None


class WalletApplicationResponse(BaseModel):
    id: int
    currency: str
    reason: Optional[str]
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)