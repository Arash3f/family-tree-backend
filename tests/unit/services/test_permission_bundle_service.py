from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.application.services.permission_bundle_service import (
    resolve_permission_ids_with_bundles,
)
from app.domain.shared.permissions import Permissions


@pytest.mark.asyncio
async def test_resolve_permission_ids_with_bundles_adds_companions():
    user_create = MagicMock()
    user_create.safe_id = UUID(int=1)
    user_create.name = Permissions.USER_CREATE

    user_read = MagicMock()
    user_read.safe_id = UUID(int=2)
    user_read.name = Permissions.USER_READ

    role_read = MagicMock()
    role_read.safe_id = UUID(int=3)
    role_read.name = Permissions.ROLE_READ

    permissions = MagicMock()
    permissions.get_or_raise = AsyncMock(return_value=user_create)
    permissions.get_by_name = AsyncMock(
        side_effect=lambda name: {
            Permissions.USER_READ: user_read,
            Permissions.ROLE_READ: role_read,
        }[name]
    )

    result = await resolve_permission_ids_with_bundles(
        permissions,
        [UUID(int=1)],
    )

    assert result == [UUID(int=1), UUID(int=3), UUID(int=2)]
    assert permissions.get_by_name.await_count == 2


@pytest.mark.asyncio
async def test_resolve_permission_ids_with_bundles_when_companion_already_present():
    user_create = MagicMock()
    user_create.safe_id = UUID(int=1)
    user_create.name = Permissions.USER_CREATE

    user_read = MagicMock()
    user_read.safe_id = UUID(int=2)
    user_read.name = Permissions.USER_READ

    role_read = MagicMock()
    role_read.safe_id = UUID(int=3)
    role_read.name = Permissions.ROLE_READ

    permissions = MagicMock()
    permissions.get_or_raise = AsyncMock(
        side_effect=[user_create, user_read, role_read]
    )
    permissions.get_by_name = AsyncMock()

    result = await resolve_permission_ids_with_bundles(
        permissions,
        [UUID(int=1), UUID(int=2), UUID(int=3)],
    )

    assert result == [UUID(int=1), UUID(int=2), UUID(int=3)]
    permissions.get_by_name.assert_not_awaited()


@pytest.mark.asyncio
async def test_resolve_permission_ids_with_bundles_empty():
    permissions = MagicMock()
    result = await resolve_permission_ids_with_bundles(permissions, [])
    assert result == []
    permissions.get_or_raise.assert_not_called()
