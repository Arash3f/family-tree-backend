from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.interfaces.token_service import TokenService
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.mcp_oauth_service import McpOAuthService
from app.application.use_cases.mcp.mcp_token_use_cases import (
    MCP_TOKEN_PREFIX,
    ResolveMcpTokenUseCase,
)
from app.core.config import settings
from app.domain.entities.user import User
from app.domain.exceptions.mcp_exceptions import (
    McpDisabledException,
    McpInvalidTokenException,
)
from app.domain.exceptions.oauth_exceptions import OAuthError
from app.domain.exceptions.user_exceptions import (
    AccountDeactivatedException,
    UserNotFoundException,
)
from app.presentation.dependencies import get_request_uow, get_token_service
from app.presentation.mcp.context import mcp_caller

_bearer = HTTPBearer(auto_error=False)


async def require_mcp_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    uow: UnitOfWork = Depends(get_request_uow),
    token_service: TokenService = Depends(get_token_service),
) -> User:
    """Authenticate an MCP request (OAuth access JWT or personal `ftmcp_…` token).

    @throws {AppException} McpDisabledException - When MCP_ENABLED is false.
    @throws {AppException} McpInvalidTokenException - Missing / bad token.
    """
    if not settings.MCP_ENABLED:
        raise McpDisabledException()

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise McpInvalidTokenException(detail=["Bearer MCP token required"])

    raw = credentials.credentials
    oauth = McpOAuthService(uow.session, token_service)

    if raw.startswith(MCP_TOKEN_PREFIX):
        user = await ResolveMcpTokenUseCase(uow, token_service).execute(raw)
    else:
        try:
            payload = oauth.decode_mcp_access_token(raw)
            user_id = UUID(str(payload["sub"]))
        except (OAuthError, ValueError, KeyError) as exc:
            raise McpInvalidTokenException(detail=["Invalid MCP access token"]) from exc

        user = await uow.users.get(user_id)
        if user is None:
            raise UserNotFoundException()
        if not user.is_active:
            raise AccountDeactivatedException()

    mcp_caller.set(user)
    request.state.mcp_user = user
    request.state.mcp_www_authenticate = oauth.www_authenticate()
    return user
