from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


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
    role_id: UUID | None = None
    role_name: str | None = None
    permissions: list[str] = []
    permission_details: list[MePermissionItem] = Field(default_factory=list)
    session_id: UUID
    account_type: str = "free"


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
