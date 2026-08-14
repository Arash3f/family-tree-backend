from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.permission import Permission


class PermissionCreateDTO(BaseModel):
    name: str
    description_en: str = ""
    description_fa: str = ""


class PermissionCreateResponseDTO(BaseModel):
    id: UUID
    name: str
    description_en: str = ""
    description_fa: str = ""


class PermissionCreateMapper(BaseModel):
    @staticmethod
    def to_response(permission: Permission) -> PermissionCreateResponseDTO:
        return PermissionCreateResponseDTO(
            id=permission.safe_id,
            name=permission.name,
            description_en=permission.description_en,
            description_fa=permission.description_fa,
        )
