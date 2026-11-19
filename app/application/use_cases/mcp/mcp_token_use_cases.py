import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.application.interfaces.token_service import TokenService
from app.application.interfaces.unit_of_work import UnitOfWork
from app.core.config import settings
from app.domain.entities.mcp_token import McpToken
from app.domain.exceptions.mcp_exceptions import (
    McpDisabledException,
    McpInvalidTokenException,
    McpTokenLimitException,
    McpTokenNotFoundException,
)
from app.domain.entities.user import User
from app.domain.exceptions.user_exceptions import (
    AccountDeactivatedException,
    UserNotFoundException,
)

MCP_TOKEN_PREFIX = "ftmcp_"


@dataclass(frozen=True)
class McpTokenCreatedDTO:
    id: UUID
    name: str
    token: str
    token_prefix: str
    expires_at: datetime | None
    created_at: datetime | None


@dataclass(frozen=True)
class McpTokenListItemDTO:
    id: UUID
    name: str
    token_prefix: str
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime | None


def _assert_mcp_enabled() -> None:
    if not settings.MCP_ENABLED:
        raise McpDisabledException()


def mint_mcp_token_secret() -> str:
    """Build a new opaque MCP secret (`ftmcp_` + url-safe random)."""
    return f"{MCP_TOKEN_PREFIX}{secrets.token_urlsafe(32)}"


class CreateMcpTokenUseCase:
    def __init__(self, uow: UnitOfWork, token_service: TokenService):
        self.uow = uow
        self.token_service = token_service

    async def execute(
        self,
        *,
        user_id: UUID,
        name: str,
        expires_in_days: int | None = None,
    ) -> McpTokenCreatedDTO:
        """Create a personal MCP token; the raw secret is returned once.

        @param user_id - Owner of the token.
        @param name - Label shown in the panel (e.g. "Claude desktop").
        @param expires_in_days - Optional lifetime; None uses MCP_TOKEN_DEFAULT_DAYS
            (0 means never expires).

        @returns The created token metadata plus the raw secret.

        @throws {AppException} McpDisabledException - When MCP_ENABLED is false.
        @throws {AppException} McpTokenLimitException - When the user already has
            MCP_TOKEN_MAX_ACTIVE live tokens.
        """
        _assert_mcp_enabled()
        label = name.strip() or "MCP token"
        if len(label) > 120:
            label = label[:120]

        days = (
            settings.MCP_TOKEN_DEFAULT_DAYS
            if expires_in_days is None
            else max(0, expires_in_days)
        )
        expires_at = (
            None
            if days == 0
            else datetime.now(UTC) + timedelta(days=days)
        )

        raw = mint_mcp_token_secret()
        token_hash = self.token_service.hash_token(raw)
        token_prefix = raw[:12]

        async with self.uow:
            active = await self.uow.mcp_tokens.count_active_by_user(user_id)
            if active >= settings.MCP_TOKEN_MAX_ACTIVE:
                raise McpTokenLimitException(
                    detail=[
                        f"limit={settings.MCP_TOKEN_MAX_ACTIVE}",
                        f"active={active}",
                    ]
                )

            created = await self.uow.mcp_tokens.create(
                McpToken(
                    user_id=user_id,
                    name=label,
                    token_hash=token_hash,
                    token_prefix=token_prefix,
                    expires_at=expires_at,
                )
            )
            await self.uow.commit()

        return McpTokenCreatedDTO(
            id=created.safe_id,
            name=created.name,
            token=raw,
            token_prefix=created.token_prefix,
            expires_at=created.expires_at,
            created_at=created.created_at,
        )


class ListMcpTokensUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, *, user_id: UUID) -> list[McpTokenListItemDTO]:
        _assert_mcp_enabled()
        async with self.uow:
            tokens = await self.uow.mcp_tokens.list_active_by_user(user_id)
        return [
            McpTokenListItemDTO(
                id=token.safe_id,
                name=token.name,
                token_prefix=token.token_prefix,
                expires_at=token.expires_at,
                last_used_at=token.last_used_at,
                created_at=token.created_at,
            )
            for token in tokens
            if token.is_active()
        ]


class RevokeMcpTokenUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, *, user_id: UUID, token_id: UUID) -> None:
        _assert_mcp_enabled()
        async with self.uow:
            token = await self.uow.mcp_tokens.get(token_id)
            if token is None or token.user_id != user_id or token.revoked_at is not None:
                raise McpTokenNotFoundException(detail=[f"token_id={token_id}"])
            await self.uow.mcp_tokens.revoke(token_id, datetime.now(UTC))
            await self.uow.commit()


class ResolveMcpTokenUseCase:
    """Authenticate an MCP request from a Bearer personal access token."""

    def __init__(self, uow: UnitOfWork, token_service: TokenService):
        self.uow = uow
        self.token_service = token_service

    async def execute(self, raw_token: str) -> User:
        """
        @param raw_token - The Bearer secret from the Authorization header.

        @returns The active user that owns the token.

        @throws {AppException} McpDisabledException - When MCP is off.
        @throws {AppException} McpInvalidTokenException - Bad / expired / revoked.
        @throws {AppException} UserNotFoundException - Owner missing.
        @throws {AppException} AccountDeactivatedException - Owner inactive.
        """
        _assert_mcp_enabled()
        if not raw_token or not raw_token.startswith(MCP_TOKEN_PREFIX):
            raise McpInvalidTokenException()

        token_hash = self.token_service.hash_token(raw_token)
        async with self.uow:
            record = await self.uow.mcp_tokens.get_by_hash(token_hash)
            if record is None or not record.is_active():
                raise McpInvalidTokenException()

            user = await self.uow.users.get(record.user_id)
            if user is None:
                raise UserNotFoundException()
            if not user.is_active:
                raise AccountDeactivatedException()

            record.touch()
            await self.uow.mcp_tokens.update(record)
            await self.uow.commit()
            return user
