from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.user import User


class UserCreateDTO(BaseModel):
    username: str
    password: str
    re_password: str
    role_id: UUID | None


class UserCreateResponseDTO(BaseModel):
    id: UUID
    username: str
    role_id: UUID | None


class UserCreateMapper(BaseModel):
    @staticmethod
    def to_response(user: User) -> UserCreateResponseDTO:
        return UserCreateResponseDTO(
            id=user.safe_id,
            username=user.username,
            role_id=user.role_id,
        )
