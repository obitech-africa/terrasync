from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    full_name: str
    email: str | None
    phone: str | None
    company: str | None
    staff_no: str | None
    role: str
    certifications: list
    active: bool


class DeviceActivationRequest(BaseModel):
    username: str = Field(min_length=2, max_length=120)
    code: str = Field(min_length=4, max_length=20)
    device_key: str = Field(min_length=8, max_length=120)
    device_name: str = Field(min_length=2, max_length=160)
    platform: str | None = Field(default=None, max_length=80)


class StaffLoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserOut
    device_id: str | None = None
    expires_at: datetime | None = None


class ActivationCodeCreate(BaseModel):
    user_id: str
    expires_minutes: int = Field(default=30, ge=1, le=1440)


class ActivationCodeIssued(BaseModel):
    user_id: str
    code: str
    expires_at: datetime


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    device_name: str
    platform: str | None
    device_key: str
    active: bool
    activated_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None
