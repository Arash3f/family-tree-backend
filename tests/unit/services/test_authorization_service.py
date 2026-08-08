from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.application.services.authorization_service import AuthorizationService


@pytest.mark.asyncio
async def test_user_has_permission_true(mock_uow):
    permission = MagicMock(name="person.create")
    permission.name = "person.create"
    role = MagicMock(permissions=[permission])
    user = MagicMock(role=role)
    mock_uow.users.get_with_details = AsyncMock(return_value=user)

    service = AuthorizationService(mock_uow)
    assert await service.user_has_permission(UUID(int=1), "person.create") is True


@pytest.mark.asyncio
async def test_user_has_permission_false_when_missing_user_or_role(mock_uow):
    mock_uow.users.get_with_details = AsyncMock(return_value=None)
    service = AuthorizationService(mock_uow)
    assert await service.user_has_permission(UUID(int=1), "person.create") is False

    mock_uow.users.get_with_details = AsyncMock(return_value=MagicMock(role=None))
    assert await service.user_has_permission(UUID(int=1), "person.create") is False


@pytest.mark.asyncio
async def test_user_has_any_permission(mock_uow):
    permission = MagicMock()
    permission.name = "person.read"
    role = MagicMock(permissions=[permission])
    user = MagicMock(role=role)
    mock_uow.users.get_with_details = AsyncMock(return_value=user)

    service = AuthorizationService(mock_uow)
    assert (
        await service.user_has_any_permission(
            UUID(int=1), ["person.create", "person.read"]
        )
        is True
    )
    assert await service.user_has_any_permission(UUID(int=1), ["role.create"]) is False
