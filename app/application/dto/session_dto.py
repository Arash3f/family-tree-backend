from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SessionListItemDTO(BaseModel):
    id: UUID
    user_agent: str | None
    ip_address: str | None
    created_at: datetime | None
    expires_at: datetime
    is_current: bool


class MeResponseDTO(BaseModel):
    id: UUID
    username: str
    role_id: UUID | None
    role_name: str | None
    permissions: list[str]
    session_id: UUID


class ChangePasswordDTO(BaseModel):
    current_password: str
    new_password: str
    re_password: str
