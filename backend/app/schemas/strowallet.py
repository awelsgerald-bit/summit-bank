from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class StroWalletAccountResponse(BaseModel):
    id: int
    nuban_account_number: Optional[str]
    bank_name: Optional[str]
    account_name: Optional[str]
    status: str
    failure_reason: Optional[str]
    created_at: datetime
    activated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)