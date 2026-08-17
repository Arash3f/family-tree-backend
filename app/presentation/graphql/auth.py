from datetime import datetime, timezone
from uuid import UUID

from fastapi import Request
from strawberry.types import Info

from app.domain.entities.user import User
from app.domain.exceptions.auth_exceptions import InvalidCredentialsException
from app.domain.exceptions.permission_exceptions import PermissionDeniedException
from app.domain.exceptions.user_exceptions import UserNotFoundException
from app.presentation.graphql.context import GraphQLContext
from app.presentation.rest.dependencies.rate_limit import rate_limit_auth


def _context(info: Info) -> GraphQLContext:
    return info.context


def _request(info: Info) -> Request:
    request = _context(info).request
    if request is None or not isinstance(request, Request):
        raise InvalidCredentialsException()
    return request


def _extract_bearer_token(info: Info) -> str:
    authorization = _request(info).headers.get("Authorization")
    if not authorization:
        raise InvalidCredentialsException()

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise InvalidCredentialsException()

    return token


async def get_current_user(info: Info) -> User:
    ctx = _context(info)
    token = _extract_bearer_token(info)

    try:
        payload = ctx.token_service.decode_token(token)

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
    except (ValueError, KeyError, TypeError) as exc:
        raise InvalidCredentialsException() from exc

    async with ctx.uow:
        session = await ctx.uow.sessions.get(session_id)
        if (
            session is None
            or session.user_id != user_id
            or not session.is_active(datetime.now(timezone.utc))
        ):
            raise InvalidCredentialsException()

        user = await ctx.uow.users.get(user_id)
        if not user:
            raise UserNotFoundException()

        user._active_session_id = session_id  # type: ignore[attr-defined]
        return user


def get_current_session_id(user: User) -> UUID:
    session_id = getattr(user, "_active_session_id", None)
    if session_id is None:
        raise InvalidCredentialsException()
    return session_id


async def require_permission(info: Info, permission: str) -> User:
    ctx = _context(info)
    user = await get_current_user(info)
    has_permission = await ctx.authorization_service.user_has_permission(
        user.safe_id,
        permission,
    )
    if not has_permission:
        raise PermissionDeniedException()
    return user


async def require_any_permission(info: Info, *permissions: str) -> User:
    ctx = _context(info)
    user = await get_current_user(info)
    has_permission = await ctx.authorization_service.user_has_any_permission(
        user.safe_id,
        list(permissions),
    )
    if not has_permission:
        raise PermissionDeniedException()
    return user


async def enforce_auth_rate_limit(info: Info) -> None:
    await rate_limit_auth(_request(info))


def client_meta(info: Info) -> tuple[str | None, str | None]:
    request = _request(info)
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    return user_agent, ip_address
