from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user_session import UserSession
from app.domain.repositories.user_session_repository import UserSessionRepository
from app.infrastructure.database.models.user_session_model import UserSessionModel


class SQLUserSessionRepository(UserSessionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, session: UserSession) -> UserSession:
        model = self._to_model(session)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get(self, session_id: UUID) -> UserSession | None:
        stmt = select(UserSessionModel).where(UserSessionModel.id == session_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_for_update(self, session_id: UUID) -> UserSession | None:
        stmt = (
            select(UserSessionModel)
            .where(UserSessionModel.id == session_id)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def update(self, session: UserSession) -> UserSession:
        stmt = select(UserSessionModel).where(UserSessionModel.id == session.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one()

        model.refresh_token_hash = session.refresh_token_hash
        model.expires_at = session.expires_at
        model.revoked_at = session.revoked_at
        model.replaced_by_id = session.replaced_by_id
        model.user_agent = session.user_agent
        model.ip_address = session.ip_address

        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def revoke(self, session_id: UUID, revoked_at: datetime) -> None:
        stmt = (
            update(UserSessionModel)
            .where(
                UserSessionModel.id == session_id,
                UserSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        await self.session.execute(stmt)

    async def revoke_all_for_user(self, user_id: UUID, revoked_at: datetime) -> int:
        stmt = (
            update(UserSessionModel)
            .where(
                UserSessionModel.user_id == user_id,
                UserSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        result = cast(CursorResult[Any], await self.session.execute(stmt))
        return result.rowcount or 0

    def _to_entity(self, model: UserSessionModel) -> UserSession:
        return UserSession(
            id=model.id,
            user_id=model.user_id,
            refresh_token_hash=model.refresh_token_hash,
            expires_at=model.expires_at,
            revoked_at=model.revoked_at,
            replaced_by_id=model.replaced_by_id,
            user_agent=model.user_agent,
            ip_address=model.ip_address,
        )

    def _to_model(self, entity: UserSession) -> UserSessionModel:
        return UserSessionModel(
            id=entity.id,
            user_id=entity.user_id,
            refresh_token_hash=entity.refresh_token_hash,
            expires_at=entity.expires_at,
            revoked_at=entity.revoked_at,
            replaced_by_id=entity.replaced_by_id,
            user_agent=entity.user_agent,
            ip_address=entity.ip_address,
        )
