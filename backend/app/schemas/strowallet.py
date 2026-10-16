from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StroWalletApplyRequest(BaseModel):
    # Optional: lets users who registered without a phone number supply one when applying.
    phone: Optional[str] = Field(default=None, max_length=20)


class StroWalletAccountResponse(BaseModel):
    id: int
    nuban_account_number: Optional[str]
    bank_name: Optional[str]
    account_name: Optional[str]
    provider: Optional[str]
    mode: str
    status: str
    created_at: datetime
    activated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)