from typing import List

from pydantic import BaseModel

from app.infrastructure.database.models.user_model import UserModel


class _Permission(BaseModel):
    id: int
    name: str


class _RoleData(BaseModel):
    id: int
    name: str
    permissions: List[_Permission]


class UserGetWithDetailResponseDTO(BaseModel):
    id: int
    username: str
    role_id: int | None
    role: _RoleData | None

    @classmethod
    def from_model(cls, model: UserModel):
        role = None

        if model.role:
            role = _RoleData(
                id=model.role.id,
                name=model.role.name,
                permissions=[
                    _Permission(id=p.id, name=p.name) for p in model.role.permissions
                ],
            )

        return cls(
            id=model.id,
            username=model.username,
            role_id=model.role_id,
            role=role,
        )
