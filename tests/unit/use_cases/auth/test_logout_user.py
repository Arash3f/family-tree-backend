from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.application.use_cases.logout_user import LogoutAllUseCase, LogoutUseCase
from app.domain.exceptions.auth_exceptions import InvalidCredentialsException


@pytest.mark.asyncio
async def test_logout_success(mock_uow):
    session_id = UUID(int=1)
    user_id = UUID(int=2)
    session = MagicMock(user_id=user_id, revoked_at=None)
    mock_uow.sessions.get = AsyncMock(return_value=session)

    result = await LogoutUseCase(mock_uow).execute(session_id, user_id)

    assert result.result == "Logged out successfully"
    mock_uow.sessions.revoke.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_logout_already_revoked_skips_revoke(mock_uow):
    session_id = UUID(int=1)
    user_id = UUID(int=2)
    session = MagicMock(user_id=user_id, revoked_at=datetime.now(timezone.utc))
    mock_uow.sessions.get = AsyncMock(return_value=session)

    result = await LogoutUseCase(mock_uow).execute(session_id, user_id)

    assert result.result == "Logged out successfully"
    mock_uow.sessions.revoke.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_logout_invalid_session(mock_uow):
    mock_uow.sessions.get = AsyncMock(return_value=None)

    with pytest.raises(InvalidCredentialsException):
        await LogoutUseCase(mock_uow).execute(UUID(int=1), UUID(int=2))


@pytest.mark.asyncio
async def test_logout_wrong_user(mock_uow):
    session = MagicMock(user_id=UUID(int=9), revoked_at=None)
    mock_uow.sessions.get = AsyncMock(return_value=session)

    with pytest.raises(InvalidCredentialsException):
        await LogoutUseCase(mock_uow).execute(UUID(int=1), UUID(int=2))


@pytest.mark.asyncio
async def test_logout_all(mock_uow):
    mock_uow.sessions.revoke_all_for_user = AsyncMock(return_value=3)

    result = await LogoutAllUseCase(mock_uow).execute(UUID(int=2))

    assert result.result == "Revoked 3 session(s)"
    mock_uow.commit.assert_awaited_once()
