from app.application.dto.user.user_create_dto import (
    UserCreateDTO,
    UserCreateMapper,
    UserCreateResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.user import User
from app.domain.services.password_hasher import PasswordHasher


class CreateUserUseCase:
    def __init__(self, uow: UnitOfWork, password_hasher: PasswordHasher):
        self.uow = uow
        self.password_hasher = password_hasher

    async def execute(self, dto: UserCreateDTO) -> UserCreateResponseDTO:
        async with self.uow:
            role_id = None
            if dto.role_id:
                role = await self.uow.roles.get_or_raise(role_id=dto.role_id)
                role_id = role.id

            hashed_password = self.password_hasher.hash(dto.password)

            user = User(
                username=dto.username, role_id=role_id, password_hash=hashed_password
            )

            user = await self.uow.users.create(user)

            await self.uow.commit()

            return UserCreateMapper.to_response(user)
