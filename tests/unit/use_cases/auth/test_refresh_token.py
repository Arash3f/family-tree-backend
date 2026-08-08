from datetime import datetime, timedelta, timezone
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_cases.refresh_token import RefreshTokenUseCase
from app.domain.entities.user_session import UserSession
from app.domain.exceptions.auth_exceptions import InvalidCredentialsException


@pytest.mark.asyncio
async def test_refresh_rotates_session(mock_uow):
    session_id = UUID(int=10)
    user_id = UUID(int=1)

    session = UserSession(
        id=session_id,
        user_id=user_id,
        refresh_token_hash="old_hash",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    user = MagicMock()
    user.safe_id = user_id

    mock_uow.sessions.get_for_update = AsyncMock(return_value=session)
    mock_uow.sessions.create = AsyncMock()
    mock_uow.sessions.update = AsyncMock()
    mock_uow.users.get = AsyncMock(return_value=user)

    token_service = MagicMock()
    token_service.decode_token.return_value = {
        "type": "refresh",
        "sub": str(user_id),
        "sid": str(session_id),
    }
    token_service.hash_token.side_effect = ["old_hash", "new_hash"]
    token_service.create_access_token.return_value = "new_access"
    token_service.create_refresh_token.return_value = "new_refresh"

    result = await RefreshTokenUseCase(mock_uow, token_service).execute("old_refresh")

    assert result.access_token == "new_access"
    assert result.refresh_token == "new_refresh"
    assert session.revoked_at is not None
    assert session.replaced_by_id is not None
    mock_uow.sessions.create.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_reuse_revokes_all(mock_uow):
    session_id = UUID(int=10)
    user_id = UUID(int=1)

    session = UserSession(
        id=session_id,
        user_id=user_id,
        refresh_token_hash="old_hash",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        revoked_at=datetime.now(timezone.utc),
    )

    mock_uow.sessions.get_for_update = AsyncMock(return_value=session)
    mock_uow.sessions.revoke_all_for_user = AsyncMock(return_value=2)

    token_service = MagicMock()
    token_service.decode_token.return_value = {
        "type": "refresh",
        "sub": str(user_id),
        "sid": str(session_id),
    }
    token_service.hash_token.return_value = "old_hash"

    with pytest.raises(InvalidCredentialsException):
        await RefreshTokenUseCase(mock_uow, token_service).execute("stolen_refresh")

    mock_uow.sessions.revoke_all_for_user.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()
