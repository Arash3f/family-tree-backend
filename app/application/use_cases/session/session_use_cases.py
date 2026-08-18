from datetime import UTC, datetime
from uuid import UUID

from app.application.dto.session_dto import SessionListItemDTO
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.exceptions.auth_exceptions import SessionNotFoundException
from app.domain.exceptions.user_exceptions import UserNotFoundException
from app.domain.shared.dto.common_dto import ResultDTO


class ListUserSessionsUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(
        self,
        user_id: UUID,
        *,
        current_session_id: UUID | None = None,
    ) -> list[SessionListItemDTO]:
        async with self.uow:
            user = await self.uow.users.get(user_id)
            if not user:
                raise UserNotFoundException(detail=[f"user id is {user_id}"])

            sessions = await self.uow.sessions.list_active_by_user(user_id)
            return [
                SessionListItemDTO(
                    id=session.safe_id,
                    user_agent=session.user_agent,
                    ip_address=session.ip_address,
                    created_at=session.created_at,
                    expires_at=session.expires_at,
                    is_current=current_session_id is not None
                    and session.safe_id == current_session_id,
                )
                for session in sessions
            ]


class RevokeUserSessionUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, *, user_id: UUID, session_id: UUID) -> ResultDTO:
        async with self.uow:
            session = await self.uow.sessions.get(session_id)
            if session is None or session.user_id != user_id:
                raise SessionNotFoundException()

            if session.revoked_at is None:
                await self.uow.sessions.revoke(session_id, datetime.now(UTC))
                await self.uow.commit()

            return ResultDTO(result="Session revoked")


class RevokeAllUserSessionsUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, user_id: UUID) -> ResultDTO:
        async with self.uow:
            user = await self.uow.users.get(user_id)
            if not user:
                raise UserNotFoundException(detail=[f"user id is {user_id}"])

            count = await self.uow.sessions.revoke_all_for_user(
                user_id, datetime.now(UTC)
            )
            await self.uow.commit()
            return ResultDTO(result=f"Revoked {count} session(s)")
