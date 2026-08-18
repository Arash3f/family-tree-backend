from uuid import UUID

from app.application.dto.user.user_update_dto import (
    UserUpdateDTO,
    UserUpdateField,
    UserUpdateMapper,
    UserUpdateResponseDTO,
)
from app.application.interfaces.unit_of_work import UnitOfWork
from app.core.config import settings
from app.domain.entities.user import User
from app.domain.exceptions.user_exceptions import (
    PasswordConfirmationMismatchException,
    PrivilegedUserModificationException,
    SelfRoleChangeException,
)
from app.domain.services.password_hasher import PasswordHasher
from app.domain.shared.account_type import AccountType


class UpdateUserUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: PasswordHasher,
        current_user: User,
    ):
        self.uow = uow
        self.password_hasher = password_hasher
        self.current_user = current_user

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
                await self._authorize_role_change(target=user, new_role_id=role_id)
                role = await self.uow.roles.get_or_raise(role_id=role_id)
                user.role_id = role.safe_id

            if password is not None:
                if password != re_password:
                    raise PasswordConfirmationMismatchException()
                user.password_hash = self.password_hasher.hash(password)

            for field, value in update_data_enum.items():
                if field is UserUpdateField.ACCOUNT_TYPE:
                    user.account_type = AccountType(value)
                else:
                    setattr(user, field.value, value)

            user = await self.uow.users.update(user=user)

            await self.uow.commit()

            return UserUpdateMapper.to_response(user=user)

    async def _authorize_role_change(self, target: User, new_role_id: UUID) -> None:
        """Guard the two ways a role change can escalate privileges."""
        caller = self.current_user

        if target.safe_id == caller.safe_id:
            raise SelfRoleChangeException()

        caller_is_admin = await self._is_admin_role(caller.role_id)
        if caller_is_admin:
            return

        # A non-admin may neither hand out the admin role nor take it away.
        if await self._is_admin_role(new_role_id) or await self._is_admin_role(
            target.role_id
        ):
            raise PrivilegedUserModificationException()

    async def _is_admin_role(self, role_id: UUID | None) -> bool:
        if role_id is None:
            return False
        role = await self.uow.roles.get(role_id=role_id)
        if role is None:
            return False
        return role.name.strip().lower() == settings.ADMIN_ROLE_NAME.strip().lower()
