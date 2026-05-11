from pydantic import BaseModel

from app.domain.entities.permission import Permission


class PermissionGetResponseDTO(BaseModel):
    id: int
    name: str


class PermissionGetMapper(BaseModel):
    @staticmethod
    def to_response(permission: Permission) -> PermissionGetResponseDTO:
        return PermissionGetResponseDTO(
            id=permission.safe_id,
            name=permission.name,
        )
