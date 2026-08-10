from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
import hmac

from app.application.dto.auth_dto import LoginResponseDTO
from app.application.interfaces.token_service import TokenService
from app.application.interfaces.unit_of_work import UnitOfWork
from app.core.config import settings
from app.domain.entities.user_session import UserSession
from app.domain.exceptions.auth_exceptions import InvalidCredentialsException


class RefreshTokenUseCase:
    def __init__(self, uow: UnitOfWork, token_service: TokenService):
        self.uow = uow
        self.token_service = token_service

    async def execute(
        self,
        refresh_token: str,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> LoginResponseDTO:
        try:
            payload = self.token_service.decode_token(refresh_token)
        except Exception as exc:
            raise InvalidCredentialsException() from exc

        if payload.get("type") != "refresh":
            raise InvalidCredentialsException()

        user_id_raw = payload.get("sub")
        session_id_raw = payload.get("sid") or payload.get("jti")
        if user_id_raw is None or session_id_raw is None:
            raise InvalidCredentialsException()

        user_id = UUID(str(user_id_raw))
        session_id = UUID(str(session_id_raw))
        token_hash = self.token_service.hash_token(refresh_token)

        async with self.uow:
            session = await self.uow.sessions.get_for_update(session_id)

            if session is None or session.user_id != user_id:
                raise InvalidCredentialsException()

            # Stolen token reuse after rotation → revoke all sessions for the user
            if session.revoked_at is not None:
                await self.uow.sessions.revoke_all_for_user(
                    user_id, datetime.now(timezone.utc)
                )
                await self.uow.commit()
                raise InvalidCredentialsException(
                    detail=["refresh token reuse detected"]
                )

            if not session.is_active():
                raise InvalidCredentialsException()

            if not hmac.compare_digest(session.refresh_token_hash, token_hash):
                await self.uow.sessions.revoke_all_for_user(
                    user_id, datetime.now(timezone.utc)
                )
                await self.uow.commit()
                raise InvalidCredentialsException()

            user = await self.uow.users.get(user_id)
            if not user:
                raise InvalidCredentialsException()

            new_session_id = uuid4()
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
            )

            access = self.token_service.create_access_token(
                user.safe_id, new_session_id
            )
            new_refresh = self.token_service.create_refresh_token(
                user.safe_id, new_session_id
            )

            new_session = UserSession(
                id=new_session_id,
                user_id=user.safe_id,
                refresh_token_hash=self.token_service.hash_token(new_refresh),
                expires_at=expires_at,
                user_agent=user_agent or session.user_agent,
                ip_address=ip_address or session.ip_address,
            )
            await self.uow.sessions.create(new_session)

            session.revoke()
            session.replaced_by_id = new_session_id
            await self.uow.sessions.update(session)

            await self.uow.commit()

            return LoginResponseDTO(access_token=access, refresh_token=new_refresh)
