from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ExchangeRateResponse(BaseModel):
    currency: str
    rate_usd: Decimal
    source: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ManualRateRequest(BaseModel):
    rate_usd: Decimal = Field(gt=0)