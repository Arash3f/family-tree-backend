from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.application.interfaces.token_service import TokenService
from app.application.use_cases.mcp.mcp_token_use_cases import (
    CreateMcpTokenUseCase,
    ListMcpTokensUseCase,
    RevokeMcpTokenUseCase,
)
from app.core.config import settings
from app.domain.entities.user import User
from app.domain.exceptions.mcp_exceptions import McpDisabledException
from app.presentation.dependencies import get_request_uow, get_token_service
from app.presentation.mcp.protocol import list_tool_names
from app.presentation.rest.dependencies.auth_dependencies import get_current_user
from app.presentation.rest.schemas.dto.common import ResultResponse

router = APIRouter(prefix="/auth/mcp-tokens", tags=["Auth", "MCP"])


class McpTokenCreateRequest(BaseModel):
    name: str = Field(default="MCP token", max_length=120)
    expires_in_days: int | None = Field(
        default=None,
        ge=0,
        le=3650,
        description="0 = never expires; omit to use server default",
    )


class McpTokenCreatedResponse(BaseModel):
    id: UUID
    name: str
    token: str
    token_prefix: str
    expires_at: str | None
    created_at: str | None


class McpTokenResponse(BaseModel):
    id: UUID
    name: str
    token_prefix: str
    expires_at: str | None
    last_used_at: str | None
    created_at: str | None


class McpStatusResponse(BaseModel):
    enabled: bool
    endpoint: str
    tools: list[str]
    max_active_tokens: int
    default_expires_days: int


def _iso(value) -> str | None:
    return value.isoformat() if value is not None else None


@router.get("/status", response_model=McpStatusResponse)
async def mcp_status(
    _current_user: User = Depends(get_current_user),
) -> McpStatusResponse:
    return McpStatusResponse(
        enabled=settings.MCP_ENABLED,
        endpoint=settings.mcp_public_url or "/mcp",
        tools=list_tool_names(),
        max_active_tokens=settings.MCP_TOKEN_MAX_ACTIVE,
        default_expires_days=settings.MCP_TOKEN_DEFAULT_DAYS,
    )


@router.get("", response_model=list[McpTokenResponse])
async def list_mcp_tokens(
    current_user: User = Depends(get_current_user),
    uow=Depends(get_request_uow),
) -> list[McpTokenResponse]:
    if not settings.MCP_ENABLED:
        raise McpDisabledException()
    items = await ListMcpTokensUseCase(uow).execute(user_id=current_user.safe_id)
    return [
        McpTokenResponse(
            id=item.id,
            name=item.name,
            token_prefix=item.token_prefix,
            expires_at=_iso(item.expires_at),
            last_used_at=_iso(item.last_used_at),
            created_at=_iso(item.created_at),
        )
        for item in items
    ]


@router.post("", response_model=McpTokenCreatedResponse, status_code=201)
async def create_mcp_token(
    body: McpTokenCreateRequest,
    current_user: User = Depends(get_current_user),
    uow=Depends(get_request_uow),
    token_service: TokenService = Depends(get_token_service),
) -> McpTokenCreatedResponse:
    created = await CreateMcpTokenUseCase(uow, token_service).execute(
        user_id=current_user.safe_id,
        name=body.name,
        expires_in_days=body.expires_in_days,
    )
    return McpTokenCreatedResponse(
        id=created.id,
        name=created.name,
        token=created.token,
        token_prefix=created.token_prefix,
        expires_at=_iso(created.expires_at),
        created_at=_iso(created.created_at),
    )


@router.delete("/{token_id}", response_model=ResultResponse)
async def revoke_mcp_token(
    token_id: UUID,
    current_user: User = Depends(get_current_user),
    uow=Depends(get_request_uow),
) -> ResultResponse:
    await RevokeMcpTokenUseCase(uow).execute(
        user_id=current_user.safe_id, token_id=token_id
    )
    return ResultResponse(result="ok")
