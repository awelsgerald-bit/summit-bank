from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class KYCSubmissionCreate(BaseModel):
    full_legal_name: str = Field(min_length=2, max_length=150)
    date_of_birth: str  # "YYYY-MM-DD"
    id_type: str
    id_number: str = Field(min_length=1, max_length=50)
    address: str = Field(min_length=1)


class KYCSubmissionResponse(BaseModel):
    id: int
    full_legal_name: str
    date_of_birth: str
    id_type: str
    id_number: str
    address: str
    status: str
    rejection_reason: Optional[str]
    created_at: datetime
    reviewed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class KYCRejectRequest(BaseModel):
    reason: Optional[str] = None