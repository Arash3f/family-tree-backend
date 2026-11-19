from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.mcp_token import McpToken
from app.domain.repositories.mcp_token_repository import McpTokenRepository
from app.infrastructure.database.models.mcp_token_model import McpTokenModel


class SQLMcpTokenRepository(McpTokenRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, token: McpToken) -> McpToken:
        model = self._to_model(token)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get(self, token_id: UUID) -> McpToken | None:
        stmt = select(McpTokenModel).where(McpTokenModel.id == token_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_hash(self, token_hash: str) -> McpToken | None:
        stmt = select(McpTokenModel).where(McpTokenModel.token_hash == token_hash)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, token: McpToken) -> McpToken:
        stmt = select(McpTokenModel).where(McpTokenModel.id == token.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        model.name = token.name
        model.expires_at = token.expires_at
        model.revoked_at = token.revoked_at
        model.last_used_at = token.last_used_at
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def revoke(self, token_id: UUID, revoked_at: datetime) -> None:
        stmt = (
            update(McpTokenModel)
            .where(
                McpTokenModel.id == token_id,
                McpTokenModel.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        await self.session.execute(stmt)

    async def list_active_by_user(self, user_id: UUID) -> list[McpToken]:
        stmt = (
            select(McpTokenModel)
            .where(
                McpTokenModel.user_id == user_id,
                McpTokenModel.revoked_at.is_(None),
            )
            .order_by(McpTokenModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return [self._to_entity(model) for model in result.scalars().all()]

    async def count_active_by_user(self, user_id: UUID) -> int:
        stmt = select(func.count()).select_from(McpTokenModel).where(
            McpTokenModel.user_id == user_id,
            McpTokenModel.revoked_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    @staticmethod
    def _to_entity(model: McpTokenModel) -> McpToken:
        return McpToken(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            token_hash=model.token_hash,
            token_prefix=model.token_prefix,
            expires_at=model.expires_at,
            revoked_at=model.revoked_at,
            last_used_at=model.last_used_at,
            created_at=model.created_at,
        )

    @staticmethod
    def _to_model(entity: McpToken) -> McpTokenModel:
        model = McpTokenModel(
            user_id=entity.user_id,
            name=entity.name,
            token_hash=entity.token_hash,
            token_prefix=entity.token_prefix,
            expires_at=entity.expires_at,
            revoked_at=entity.revoked_at,
            last_used_at=entity.last_used_at,
        )
        if entity.id is not None:
            model.id = entity.id
        return model
