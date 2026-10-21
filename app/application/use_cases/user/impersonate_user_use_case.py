import logging
from uuid import UUID

from app.application.interfaces.token_service import TokenService
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.exceptions.user_exceptions import (
    AccountDeactivatedException,
    ImpersonationNotAllowedException,
)
from app.domain.shared.permissions import Permissions

logger = logging.getLogger(__name__)


class ImpersonateUserUseCase:
    """Issues an access token that signs an admin in as another user.

    No password is checked and no login session is opened: the returned token
    carries the impersonation flag and expires on its own (see
    `IMPERSONATION_TOKEN_EXPIRE_MINUTES`). Because nothing is stored, the token
    cannot be revoked early, which is why the lifetime is deliberately short.
    """

    def __init__(self, uow: UnitOfWork, token_service: TokenService):
        self.uow = uow
        self.token_service = token_service

    async def execute(self, *, actor_admin_id: UUID, target_user_id: UUID) -> str:
        """Mint an impersonation token for `target_user_id`.

        @param actor_admin_id - The caller, already checked for
            `Permissions.USER_IMPERSONATE` by the route guard.
        @param target_user_id - The user to be impersonated.

        @returns A signed, short-lived access token for the target user.

        @throws {AppException} ImpersonationNotAllowedException - When the
            target is the caller themselves, or is privileged enough to hold
            `USER_IMPERSONATE` (impersonating another admin would be an
            escalation path).
        @throws {AppException} UserNotFoundException - When no such user exists.
        @throws {AppException} AccountDeactivatedException - When the target
            account is deactivated.
        """
        async with self.uow:
            if target_user_id == actor_admin_id:
                raise ImpersonationNotAllowedException(
                    detail=["cannot impersonate yourself"]
                )

            target = await self.uow.users.get_or_raise(user_id=target_user_id)

            if not target.is_active:
                raise AccountDeactivatedException()

            privileged = await self.uow.users.ids_having_permission(
                [target_user_id], Permissions.USER_IMPERSONATE
            )
            if target_user_id in privileged:
                raise ImpersonationNotAllowedException(
                    detail=["target may impersonate others"]
                )

            token = self.token_service.create_impersonation_token(
                target_user_id=target_user_id,
                actor_admin_id=actor_admin_id,
            )

            # Impersonation leaves no session row, so this log line is the only
            # trace that it happened — keep it at warning so it is retained.
            logger.warning(
                "impersonation: admin %s is now acting as user %s",
                actor_admin_id,
                target_user_id,
            )
            return token
