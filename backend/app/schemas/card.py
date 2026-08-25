from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CardApplicationCreate(BaseModel):
    card_type: str = Field(default="virtual")  # "virtual" or "physical"


class CardApplicationResponse(BaseModel):
    id: int
    card_type: str
    status: str
    card_number: Optional[str]
    expiry_month: Optional[int]
    expiry_year: Optional[int]
    cvv: Optional[str]
    created_at: datetime
    approved_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)