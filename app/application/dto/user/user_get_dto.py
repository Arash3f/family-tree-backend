from pydantic import BaseModel

from app.domain.entities.user import User


class UserGetResponseDTO(BaseModel):
    id: int
    username: str
    role_id: int | None


class UserGetMapper(BaseModel):
    @staticmethod
    def to_response(user: User) -> UserGetResponseDTO:
        return UserGetResponseDTO(
            id=user.safe_id,
            username=user.username,
            role_id=user.role_id,
        )
