from uuid import UUID

from app.application.dto.session_dto import ChangePasswordDTO, MeResponseDTO
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.exceptions.user_exceptions import (
    PasswordConfirmationMismatchException,
    UserPasswordIncorectException,
)
from app.domain.services.password_hasher import PasswordHasher
from app.domain.shared.dto.common_dto import ResultDTO


class GetMeUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, user_id: UUID, session_id: UUID) -> MeResponseDTO:
        async with self.uow:
            details = await self.uow.users.get_with_details(user_id)
            if details is None:
                # Should not happen for an authenticated caller, but keep shape safe.
                user = await self.uow.users.get_or_raise(user_id)
                return MeResponseDTO(
                    id=user.safe_id,
                    username=user.username,
                    role_id=user.role_id,
                    role_name=None,
                    permissions=[],
                    session_id=session_id,
                )

            permissions: list[str] = []
            role_name = None
            if details.role is not None:
                role_name = details.role.name
                permissions = sorted(p.name for p in details.role.permissions)

            return MeResponseDTO(
                id=details.id,
                username=details.username,
                role_id=details.role_id,
                role_name=role_name,
                permissions=permissions,
                session_id=session_id,
            )


class ChangeOwnPasswordUseCase:
    def __init__(self, uow: UnitOfWork, password_hasher: PasswordHasher):
        self.uow = uow
        self.password_hasher = password_hasher

    async def execute(self, user_id: UUID, data: ChangePasswordDTO) -> ResultDTO:
        if data.new_password != data.re_password:
            raise PasswordConfirmationMismatchException()

        async with self.uow:
            user = await self.uow.users.get_or_raise(user_id)

            if not self.password_hasher.verify(
                data.current_password, user.password_hash
            ):
                raise UserPasswordIncorectException()

            user.password_hash = self.password_hasher.hash(data.new_password)
            await self.uow.users.update(user)
            await self.uow.commit()

            return ResultDTO(result="Password updated")
