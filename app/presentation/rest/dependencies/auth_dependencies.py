from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose.exceptions import JWTError

from app.application.interfaces.token_service import TokenService
from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.exceptions.auth_exceptions import InvalidCredentialsException
from app.domain.exceptions.user_exceptions import (
    AccountDeactivatedException,
    UserNotFoundException,
)
from app.presentation.dependencies import get_request_uow, get_token_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
# auto_error=False so a request with no Authorization header reaches the
# dependency as None instead of being rejected at the security layer.
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    uow: UnitOfWork = Depends(get_request_uow),
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
    except (JWTError, ValueError, KeyError, TypeError) as exc:
        raise InvalidCredentialsException() from exc

    session = await uow.sessions.get(session_id)
    if (
        session is None
        or session.user_id != user_id
        or not session.is_active(datetime.now(UTC))
    ):
        raise InvalidCredentialsException()

    user = await uow.users.get(user_id)

    if not user:
        raise UserNotFoundException()

    if not user.is_active:
        raise AccountDeactivatedException()

    # Attach session id for logout handlers
    user._active_session_id = session_id  # type: ignore[attr-defined]
    return user


async def get_optional_current_user(
    token: str | None = Depends(oauth2_scheme_optional),
    uow: UnitOfWork = Depends(get_request_uow),
    token_service: TokenService = Depends(get_token_service),
):
    """Resolve the caller when there is one, without requiring it.

    Only the *absence* of a token is treated as anonymous. A token that is
    present but bad still raises: silently downgrading an expired session to
    'anonymous' would show a signed-in member the public view of a tree and
    never tell them why.

    @param token - Bearer token, or None when the header is absent.

    @returns The authenticated user, or None for an anonymous caller.

    @throws {AppException} InvalidCredentialsException - When a token is present
        but not a valid, active access token.
    @throws {AppException} UserNotFoundException - When it names a missing user.
    @throws {AppException} AccountDeactivatedException - When that user is inactive.
    """
    if token is None:
        return None
    return await get_current_user(token=token, uow=uow, token_service=token_service)


def get_current_session_id(current_user=Depends(get_current_user)) -> UUID:
    session_id = getattr(current_user, "_active_session_id", None)
    if session_id is None:
        raise InvalidCredentialsException()
    return session_id
