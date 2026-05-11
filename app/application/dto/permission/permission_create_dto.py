from pydantic import BaseModel

from app.domain.entities.permission import Permission


class PermissionCreateDTO(BaseModel):
    name: str


class PermissionCreateResponseDTO(BaseModel):
    id: int
    name: str


class PermissionCreateMapper(BaseModel):
    @staticmethod
    def to_response(permission: Permission) -> PermissionCreateResponseDTO:
        return PermissionCreateResponseDTO(
            id=permission.safe_id,
            name=permission.name,
        )
