from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: UUID
    username: str
    role_id: UUID | None = None
    role_name: str | None = None
    permissions: list[str] = []
    session_id: UUID


class SessionResponse(BaseModel):
    id: UUID
    user_agent: str | None = None
    ip_address: str | None = None
    created_at: datetime | None = None
    expires_at: datetime
    is_current: bool = False


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    re_password: str
