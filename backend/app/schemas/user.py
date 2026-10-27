from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone_number: str = Field(min_length=10, max_length=20)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    account_number: str
    balance: Decimal
    role: str
    created_at: datetime
    kyc_status: str
    phone_number: Optional[str] = None
    avatar: Optional[str] = None
    has_pin: bool = False

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    phone_number: Optional[str] = Field(default=None, min_length=10, max_length=20)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class AvatarUpdate(BaseModel):
    image: str = Field(min_length=20, max_length=300_000)



class PinSet(BaseModel):
    password: str = Field(min_length=1, max_length=128)  # the account password, to prove it is you
    new_pin: str = Field(pattern=r"^\d{4,6}$")
