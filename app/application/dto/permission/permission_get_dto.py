from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.permission import Permission


class PermissionGetResponseDTO(BaseModel):
    id: UUID
    name: str
    description_en: str = ""
    description_fa: str = ""


class PermissionGetMapper(BaseModel):
    @staticmethod
    def to_response(permission: Permission) -> PermissionGetResponseDTO:
        return PermissionGetResponseDTO(
            id=permission.safe_id,
            name=permission.name,
            description_en=permission.description_en,
            description_fa=permission.description_fa,
        )
