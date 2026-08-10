from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.application.dto.auth_dto import LoginDTO, LoginResponseDTO
from app.application.interfaces.token_service import TokenService
from app.application.interfaces.unit_of_work import UnitOfWork
from app.core.config import settings
from app.domain.entities.user_session import UserSession
from app.domain.exceptions.auth_exceptions import InvalidCredentialsException
from app.domain.services.password_hasher import PasswordHasher


class LoginUserUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ):
        self.uow = uow
        self.password_hasher = password_hasher
        self.token_service = token_service

    async def execute(
        self,
        data: LoginDTO,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> LoginResponseDTO:
        async with self.uow:
            user = await self.uow.users.get_by_username(data.username)

            if not user:
                raise InvalidCredentialsException()

            if not self.password_hasher.verify(data.password, user.password_hash):
                raise InvalidCredentialsException()

            session_id = uuid4()
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
            )

            access = self.token_service.create_access_token(user.safe_id, session_id)
            refresh = self.token_service.create_refresh_token(user.safe_id, session_id)

            session = UserSession(
                id=session_id,
                user_id=user.safe_id,
                refresh_token_hash=self.token_service.hash_token(refresh),
                expires_at=expires_at,
                user_agent=user_agent,
                ip_address=ip_address,
            )
            await self.uow.sessions.create(session)
            await self.uow.commit()

            return LoginResponseDTO(access_token=access, refresh_token=refresh)
