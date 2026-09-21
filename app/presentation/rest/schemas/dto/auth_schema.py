from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_.-]+$",
    )
    fullname: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=256)
    re_password: str = Field(min_length=8, max_length=256)
    email: str | None = Field(
        default=None,
        max_length=255,
        pattern=r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$",
    )
    phone: str | None = Field(default=None, max_length=32)
    country_code: str | None = Field(default=None, max_length=8)

    @field_validator("fullname", mode="before")
    @classmethod
    def strip_fullname(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email", "phone", "country_code", mode="before")
    @classmethod
    def blank_optional_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MePermissionItem(BaseModel):
    name: str
    description_en: str = ""
    description_fa: str = ""


class MeResponse(BaseModel):
    id: UUID
    username: str
    fullname: str = ""
    email: str | None = None
    phone: str | None = None
    role_id: UUID | None = None
    role_name: str | None = None
    permissions: list[str] = []
    permission_details: list[MePermissionItem] = Field(default_factory=list)
    session_id: UUID
    account_type: str = "free"
    preferred_locale: Literal["en", "fa"] | None = None
    preferred_theme: Literal["light", "dark", "system"] | None = None


class SessionResponse(BaseModel):
    id: UUID
    user_agent: str | None = None
    ip_address: str | None = None
    created_at: datetime | None = None
    expires_at: datetime
    is_current: bool = False


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=256)
    re_password: str = Field(min_length=8, max_length=256)


class UpdatePreferencesRequest(BaseModel):
    preferred_locale: Literal["en", "fa"] | None = None
    preferred_theme: Literal["light", "dark", "system"] | None = None
