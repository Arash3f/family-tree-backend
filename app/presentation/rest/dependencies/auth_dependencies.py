from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.application.interfaces.token_service import TokenService
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.exceptions.auth_exceptions import InvalidCredentialsException
from app.domain.exceptions.user_exceptions import UserNotFoundException
from app.presentation.rest.utils.dependencies import get_token_service, get_uow

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    uow: UnitOfWork = Depends(get_uow),
    token_service: TokenService = Depends(get_token_service),
):
    try:
        payload = token_service.decode_token(token)

        if payload.get("type") != "access":
            raise InvalidCredentialsException()

        user_id_raw = payload.get("sub")
        session_id_raw = payload.get("sid")

        if user_id_raw is None or session_id_raw is None:
            raise InvalidCredentialsException()

        user_id = UUID(str(user_id_raw))
        session_id = UUID(str(session_id_raw))

    except InvalidCredentialsException:
        raise
    except Exception as exc:
        raise InvalidCredentialsException() from exc

    async with uow:
        session = await uow.sessions.get(session_id)
        if (
            session is None
            or session.user_id != user_id
            or not session.is_active(datetime.now(timezone.utc))
        ):
            raise InvalidCredentialsException()

        user = await uow.users.get(user_id)

        if not user:
            raise UserNotFoundException()

        # Attach session id for logout handlers
        user._active_session_id = session_id  # type: ignore[attr-defined]
        return user


def get_current_session_id(current_user=Depends(get_current_user)) -> UUID:
    session_id = getattr(current_user, "_active_session_id", None)
    if session_id is None:
        raise InvalidCredentialsException()
    return session_id
