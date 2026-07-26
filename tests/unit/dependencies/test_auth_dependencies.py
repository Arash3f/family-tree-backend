from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.domain.exceptions.auth_exceptions import InvalidCredentialsException
from app.domain.exceptions.user_exceptions import UserNotFoundException
from app.presentation.rest.dependencies.auth_dependencies import (
    get_current_session_id,
    get_current_user,
)


@pytest.mark.asyncio
async def test_get_current_user_success(mock_uow):
    user_id = UUID(int=1)
    session_id = UUID(int=2)
    token_service = MagicMock()
    token_service.decode_token.return_value = {
        "type": "access",
        "sub": str(user_id),
        "sid": str(session_id),
    }
    session = MagicMock(user_id=user_id)
    session.is_active.return_value = True
    user = MagicMock()
    mock_uow.sessions.get = AsyncMock(return_value=session)
    mock_uow.users.get = AsyncMock(return_value=user)

    result = await get_current_user("token", mock_uow, token_service)

    assert result is user
    assert result._active_session_id == session_id


@pytest.mark.asyncio
async def test_get_current_user_rejects_refresh_token(mock_uow):
    token_service = MagicMock()
    token_service.decode_token.return_value = {"type": "refresh", "sub": "1", "sid": "2"}

    with pytest.raises(InvalidCredentialsException):
        await get_current_user("token", mock_uow, token_service)


@pytest.mark.asyncio
async def test_get_current_user_missing_claims(mock_uow):
    token_service = MagicMock()
    token_service.decode_token.return_value = {"type": "access"}

    with pytest.raises(InvalidCredentialsException):
        await get_current_user("token", mock_uow, token_service)


@pytest.mark.asyncio
async def test_get_current_user_inactive_session(mock_uow):
    user_id = UUID(int=1)
    session_id = UUID(int=2)
    token_service = MagicMock()
    token_service.decode_token.return_value = {
        "type": "access",
        "sub": str(user_id),
        "sid": str(session_id),
    }
    session = MagicMock(user_id=user_id)
    session.is_active.return_value = False
    mock_uow.sessions.get = AsyncMock(return_value=session)

    with pytest.raises(InvalidCredentialsException):
        await get_current_user("token", mock_uow, token_service)


@pytest.mark.asyncio
async def test_get_current_user_not_found(mock_uow):
    user_id = UUID(int=1)
    session_id = UUID(int=2)
    token_service = MagicMock()
    token_service.decode_token.return_value = {
        "type": "access",
        "sub": str(user_id),
        "sid": str(session_id),
    }
    session = MagicMock(user_id=user_id)
    session.is_active.return_value = True
    mock_uow.sessions.get = AsyncMock(return_value=session)
    mock_uow.users.get = AsyncMock(return_value=None)

    with pytest.raises(UserNotFoundException):
        await get_current_user("token", mock_uow, token_service)


def test_get_current_session_id():
    user = MagicMock()
    user._active_session_id = UUID(int=5)
    assert get_current_session_id(user) == UUID(int=5)

    with pytest.raises(InvalidCredentialsException):
        get_current_session_id(MagicMock(spec=[]))
