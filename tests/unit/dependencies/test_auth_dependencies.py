from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from jose.exceptions import ExpiredSignatureError, JWTError

from app.domain.exceptions.auth_exceptions import InvalidCredentialsException
from app.domain.exceptions.user_exceptions import (
    AccountDeactivatedException,
    UserNotFoundException,
)
from app.presentation.rest.dependencies.auth_dependencies import (
    get_current_session_id,
    get_current_user,
    get_is_impersonating,
    get_optional_current_session_id,
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
    token_service.decode_token.return_value = {
        "type": "refresh",
        "sub": "1",
        "sid": "2",
    }

    with pytest.raises(InvalidCredentialsException):
        await get_current_user("token", mock_uow, token_service)


@pytest.mark.asyncio
async def test_get_current_user_missing_claims(mock_uow):
    token_service = MagicMock()
    token_service.decode_token.return_value = {"type": "access"}

    with pytest.raises(InvalidCredentialsException):
        await get_current_user("token", mock_uow, token_service)


@pytest.mark.asyncio
async def test_get_current_user_expired_token(mock_uow):
    token_service = MagicMock()
    token_service.decode_token.side_effect = ExpiredSignatureError(
        "Signature has expired."
    )

    with pytest.raises(InvalidCredentialsException):
        await get_current_user("token", mock_uow, token_service)


@pytest.mark.asyncio
async def test_get_current_user_invalid_jwt(mock_uow):
    token_service = MagicMock()
    token_service.decode_token.side_effect = JWTError("Invalid token")

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


@pytest.mark.asyncio
async def test_impersonation_token_needs_no_session(mock_uow):
    """An `imp` token authenticates with no session row at all."""
    user_id = UUID(int=1)
    token_service = MagicMock()
    token_service.decode_token.return_value = {
        "type": "access",
        "sub": str(user_id),
        "imp": True,
        "act": str(UUID(int=7)),
    }
    user = MagicMock(is_active=True)
    mock_uow.sessions.get = AsyncMock()
    mock_uow.users.get = AsyncMock(return_value=user)

    result = await get_current_user("token", mock_uow, token_service)

    assert result is user
    # Nothing was looked up, and no session id is attached — so the session
    # routes (logout, /me) refuse this token.
    mock_uow.sessions.get.assert_not_awaited()
    assert result._active_session_id is None


@pytest.mark.asyncio
async def test_impersonation_token_rejects_deactivated_user(mock_uow):
    token_service = MagicMock()
    token_service.decode_token.return_value = {
        "type": "access",
        "sub": str(UUID(int=1)),
        "imp": True,
    }
    mock_uow.users.get = AsyncMock(return_value=MagicMock(is_active=False))

    with pytest.raises(AccountDeactivatedException):
        await get_current_user("token", mock_uow, token_service)


@pytest.mark.asyncio
async def test_truthy_imp_claim_does_not_skip_the_session_check(mock_uow):
    """Only a real boolean `true` counts, so a crafted claim cannot pass."""
    token_service = MagicMock()
    token_service.decode_token.return_value = {
        "type": "access",
        "sub": str(UUID(int=1)),
        "imp": "yes",
    }

    with pytest.raises(InvalidCredentialsException):
        await get_current_user("token", mock_uow, token_service)


@pytest.mark.asyncio
async def test_impersonation_token_still_requires_a_subject(mock_uow):
    token_service = MagicMock()
    token_service.decode_token.return_value = {"type": "access", "imp": True}

    with pytest.raises(InvalidCredentialsException):
        await get_current_user("token", mock_uow, token_service)


def test_optional_session_id_tolerates_an_impersonated_caller():
    """`/auth/me` must still answer while impersonating, hence no raise."""
    impersonated = MagicMock()
    impersonated._active_session_id = None
    assert get_optional_current_session_id(impersonated) is None

    normal = MagicMock()
    normal._active_session_id = UUID(int=5)
    assert get_optional_current_session_id(normal) == UUID(int=5)


def test_get_is_impersonating():
    impersonated = MagicMock()
    impersonated._is_impersonated = True
    assert get_is_impersonating(impersonated) is True

    normal = MagicMock()
    normal._is_impersonated = False
    assert get_is_impersonating(normal) is False

    # A caller object that never got the attribute is not impersonating.
    assert get_is_impersonating(MagicMock(spec=[])) is False


def test_get_current_session_id_refuses_an_impersonated_caller():
    """Impersonation has no session, so session-bound routes must 401."""
    user = MagicMock()
    user._active_session_id = None

    with pytest.raises(InvalidCredentialsException):
        get_current_session_id(user)


def test_get_current_session_id():
    user = MagicMock()
    user._active_session_id = UUID(int=5)
    assert get_current_session_id(user) == UUID(int=5)

    with pytest.raises(InvalidCredentialsException):
        get_current_session_id(MagicMock(spec=[]))
