from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SessionListItemDTO(BaseModel):
    id: UUID
    user_agent: str | None
    ip_address: str | None
    created_at: datetime | None
    expires_at: datetime
    is_current: bool


class MePermissionDTO(BaseModel):
    name: str
    description_en: str = ""
    description_fa: str = ""


class MeResponseDTO(BaseModel):
    id: UUID
    username: str
    fullname: str = ""
    role_id: UUID | None
    role_name: str | None
    permissions: list[str]
    permission_details: list[MePermissionDTO] = Field(default_factory=list)
    session_id: UUID
    account_type: str


class ChangePasswordDTO(BaseModel):
    current_password: str
    new_password: str
    re_password: str
