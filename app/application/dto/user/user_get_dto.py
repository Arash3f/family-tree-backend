from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.user import User


class UserGetResponseDTO(BaseModel):
    id: UUID
    username: str
    fullname: str
    role_id: UUID | None


class UserGetMapper(BaseModel):
    @staticmethod
    def to_response(user: User) -> UserGetResponseDTO:
        return UserGetResponseDTO(
            id=user.safe_id,
            username=user.username,
            fullname=user.fullname,
            role_id=user.role_id,
        )
