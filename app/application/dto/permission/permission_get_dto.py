from pydantic import BaseModel

from app.domain.entities.permission import Permission


class PermissionGetResponseDTO(BaseModel):
    id: int
    name: str


class PermissionGetMapper(BaseModel):
    @staticmethod
    def to_response(permission: Permission) -> PermissionGetResponseDTO:
        assert permission.id is not None

        return PermissionGetResponseDTO(
            id=permission.id,
            name=permission.name,
        )
