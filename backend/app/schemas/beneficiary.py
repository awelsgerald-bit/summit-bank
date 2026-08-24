from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class BeneficiaryCreate(BaseModel):
    nickname: str = Field(min_length=1, max_length=100)
    account_number: str = Field(min_length=1, max_length=20)


class BeneficiaryResponse(BaseModel):
    id: int
    nickname: str
    account_number: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)