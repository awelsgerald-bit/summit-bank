from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaystackInitializeRequest(BaseModel):
    amount: Decimal = Field(gt=0)


class PaystackInitializeResponse(BaseModel):
    authorization_url: str
    reference: str


class PaystackPaymentResponse(BaseModel):
    id: int
    reference: str
    amount: Decimal
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)