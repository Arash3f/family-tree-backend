from app.application.dto.user.user_update_dto import (
    UserUpdateDTO,
    UserUpdateField,
    UserUpdateMapper,
    UserUpdateResponseDTO,
)
from app.application.services.unit_of_work import UnitOfWork
from app.domain.services.password_hasher import PasswordHasher


class UpdateUserUseCase:
    def __init__(self, uow: UnitOfWork, password_hasher: PasswordHasher):
        self.uow = uow
        self.password_hasher = password_hasher

    async def execute(self, dto: UserUpdateDTO) -> UserUpdateResponseDTO:
        async with self.uow:
            user = await self.uow.users.get_or_raise(user_id=dto.where.user_id)

            update_data = dto.data.model_dump(exclude_unset=True, exclude_none=True)

            update_data_enum = {
                UserUpdateField(key): value for key, value in update_data.items()
            }

            role_id = update_data_enum.pop(UserUpdateField.ROLE_ID, None)
            password = update_data_enum.pop(UserUpdateField.PASSWORD, None)
            re_password = update_data_enum.pop(UserUpdateField.RE_PASSWORD, None)

            if role_id is not None:
                role = await self.uow.roles.get_or_raise(role_id=role_id)
                user.role_id = role.safe_id

            if password is not None and re_password is not None:
                hashed_password = self.password_hasher.hash(password)
                user.password_hash = hashed_password

            for field, value in update_data_enum.items():
                setattr(user, field.value, value)

            user = await self.uow.users.update(user=user)

            await self.uow.commit()

            return UserUpdateMapper.to_response(user=user)
