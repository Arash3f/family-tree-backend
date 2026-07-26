from datetime import datetime, timezone
from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.exceptions.auth_exceptions import InvalidCredentialsException
from app.domain.shared.dto.common_dto import ResultDTO


class LogoutUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, session_id: UUID, user_id: UUID) -> ResultDTO:
        async with self.uow:
            session = await self.uow.sessions.get(session_id)
            if session is None or session.user_id != user_id:
                raise InvalidCredentialsException()

            if session.revoked_at is None:
                await self.uow.sessions.revoke(
                    session_id, datetime.now(timezone.utc)
                )
                await self.uow.commit()

            return ResultDTO(result="Logged out successfully")


class LogoutAllUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, user_id: UUID) -> ResultDTO:
        async with self.uow:
            count = await self.uow.sessions.revoke_all_for_user(
                user_id, datetime.now(timezone.utc)
            )
            await self.uow.commit()
            return ResultDTO(result=f"Revoked {count} session(s)")
