from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.interfaces.token_service import TokenService
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.use_cases.mcp.mcp_token_use_cases import ResolveMcpTokenUseCase
from app.core.config import settings
from app.domain.entities.user import User
from app.domain.exceptions.mcp_exceptions import (
    McpDisabledException,
    McpInvalidTokenException,
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
    """Authenticate an MCP request with a personal `ftmcp_…` Bearer token.

    @throws {AppException} McpDisabledException - When MCP_ENABLED is false.
    @throws {AppException} McpInvalidTokenException - Missing / bad token.
    """
    if not settings.MCP_ENABLED:
        raise McpDisabledException()

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise McpInvalidTokenException(detail=["Bearer MCP token required"])

    user = await ResolveMcpTokenUseCase(uow, token_service).execute(credentials.credentials)
    mcp_caller.set(user)
    request.state.mcp_user = user
    return user
