from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.role import Role


class RoleGetResponseDTO(BaseModel):
    id: UUID
    name: str
    permission_ids: list[UUID]


class RoleGetMapper(BaseModel):
    @staticmethod
    def to_response(role: Role) -> RoleGetResponseDTO:
        return RoleGetResponseDTO(
            id=role.safe_id,
            name=role.name,
            permission_ids=role.permission_ids,
        )
