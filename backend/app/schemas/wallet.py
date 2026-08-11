from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class WalletResponse(BaseModel):
    id: int
    currency: str
    balance: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WalletApplyRequest(BaseModel):
    currency: str  # "BTC" for now