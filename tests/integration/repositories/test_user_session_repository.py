from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.entities.role import Role
from app.domain.entities.user import User
from app.domain.entities.user_session import UserSession
from app.infrastructure.services.unit_of_work.sqlalchemy_uow import UnitOfWork


async def _create_user(uow: UnitOfWork, username: str) -> User:
    role = await uow.roles.create(
        Role(id=None, name=f"role_{username}", permission_ids=[])
    )
    return await uow.users.create(
        User(
            id=None,
            username=username,
            password_hash="hashed",
            role_id=role.safe_id,
        )
    )


@pytest.mark.asyncio
async def test_create_get_and_revoke_session(uow: UnitOfWork):
    async with uow:
        user = await _create_user(uow, "session_user")
        expires = datetime.now(UTC) + timedelta(days=7)
        created = await uow.sessions.create(
            UserSession(
                id=None,
                user_id=user.safe_id,
                refresh_token_hash="hash-create-get",
                expires_at=expires,
                user_agent="pytest",
                ip_address="127.0.0.1",
            )
        )

        fetched = await uow.sessions.get(created.safe_id)
        assert fetched is not None
        assert fetched.user_id == user.safe_id
        assert fetched.refresh_token_hash == "hash-create-get"
        assert fetched.revoked_at is None
        assert fetched.is_active()

        now = datetime.now(UTC)
        await uow.sessions.revoke(created.safe_id, revoked_at=now)
        revoked = await uow.sessions.get(created.safe_id)
        assert revoked is not None
        assert revoked.revoked_at is not None
        assert not revoked.is_active()


@pytest.mark.asyncio
async def test_get_for_update_and_update_session(uow: UnitOfWork):
    async with uow:
        user = await _create_user(uow, "session_update_user")
        created = await uow.sessions.create(
            UserSession(
                id=None,
                user_id=user.safe_id,
                refresh_token_hash="hash-before",
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
        )

        locked = await uow.sessions.get_for_update(created.safe_id)
        assert locked is not None
        locked.refresh_token_hash = "hash-after"
        locked.user_agent = "rotated"
        updated = await uow.sessions.update(locked)

        assert updated.refresh_token_hash == "hash-after"
        assert updated.user_agent == "rotated"


@pytest.mark.asyncio
async def test_revoke_all_for_user(uow: UnitOfWork):
    async with uow:
        user = await _create_user(uow, "session_revoke_all_user")
        other = await _create_user(uow, "session_other_user")
        expires = datetime.now(UTC) + timedelta(days=3)

        first = await uow.sessions.create(
            UserSession(
                id=None,
                user_id=user.safe_id,
                refresh_token_hash="hash-a",
                expires_at=expires,
            )
        )
        second = await uow.sessions.create(
            UserSession(
                id=None,
                user_id=user.safe_id,
                refresh_token_hash="hash-b",
                expires_at=expires,
            )
        )
        other_session = await uow.sessions.create(
            UserSession(
                id=None,
                user_id=other.safe_id,
                refresh_token_hash="hash-other",
                expires_at=expires,
            )
        )

        revoked_count = await uow.sessions.revoke_all_for_user(
            user.safe_id, revoked_at=datetime.now(UTC)
        )
        assert revoked_count == 2

        reloaded_first = await uow.sessions.get(first.safe_id)
        reloaded_second = await uow.sessions.get(second.safe_id)
        reloaded_other = await uow.sessions.get(other_session.safe_id)

        assert reloaded_first is not None and reloaded_first.revoked_at is not None
        assert reloaded_second is not None and reloaded_second.revoked_at is not None
        assert reloaded_other is not None and reloaded_other.revoked_at is None


@pytest.mark.asyncio
async def test_get_missing_session_returns_none(uow: UnitOfWork):
    async with uow:
        assert await uow.sessions.get(uuid4()) is None
        assert await uow.sessions.get_for_update(uuid4()) is None
