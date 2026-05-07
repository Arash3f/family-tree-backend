from pydantic import BaseModel

from app.domain.entities.user import User


class UserGetResponseDTO(BaseModel):
    id: int
    username: str
    role_id: int | None


class UserGetMapper(BaseModel):
    @staticmethod
    def to_response(user: User) -> UserGetResponseDTO:
        assert user.id is not None

        return UserGetResponseDTO(
            id=user.id,
            username=user.username,
            role_id=user.role_id,
        )
