from pydantic import BaseModel

from app.domain.entities.user import User


class UserCreateDTO(BaseModel):
    username: str
    password: str
    re_password: str
    role_id: int | None


class UserCreateResponseDTO(BaseModel):
    id: int
    username: str
    role_id: int | None


class UserCreateMapper(BaseModel):
    @staticmethod
    def to_response(user: User) -> UserCreateResponseDTO:
        assert user.id is not None

        return UserCreateResponseDTO(
            id=user.id,
            username=user.username,
            role_id=user.role_id,
        )
