from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.application.use_cases.user.impersonate_user_use_case import (
    ImpersonateUserUseCase,
)
from app.domain.exceptions.user_exceptions import (
    AccountDeactivatedException,
    ImpersonationNotAllowedException,
    UserNotFoundException,
)
from app.domain.shared.permissions import Permissions

ADMIN_ID = UUID(int=100)
TARGET_ID = UUID(int=200)


def _token_service():
    service = MagicMock()
    service.create_impersonation_token.return_value = "impersonation.jwt"
    return service


@pytest.mark.asyncio
async def test_impersonate_user_success(mock_uow):
    target = MagicMock(is_active=True)
    mock_uow.users.get_or_raise = AsyncMock(return_value=target)
    mock_uow.users.ids_having_permission = AsyncMock(return_value=set())
    token_service = _token_service()

    use_case = ImpersonateUserUseCase(mock_uow, token_service)

    token = await use_case.execute(actor_admin_id=ADMIN_ID, target_user_id=TARGET_ID)

    assert token == "impersonation.jwt"
    token_service.create_impersonation_token.assert_called_once_with(
        target_user_id=TARGET_ID, actor_admin_id=ADMIN_ID
    )
    mock_uow.users.get_or_raise.assert_awaited_once_with(user_id=TARGET_ID)


@pytest.mark.asyncio
async def test_impersonate_user_opens_no_session(mock_uow):
    """The whole point: nothing is written, so nothing can be revoked later."""
    mock_uow.users.get_or_raise = AsyncMock(return_value=MagicMock(is_active=True))
    mock_uow.users.ids_having_permission = AsyncMock(return_value=set())

    use_case = ImpersonateUserUseCase(mock_uow, _token_service())

    await use_case.execute(actor_admin_id=ADMIN_ID, target_user_id=TARGET_ID)

    mock_uow.sessions.create.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_impersonate_self_is_refused(mock_uow):
    use_case = ImpersonateUserUseCase(mock_uow, _token_service())

    with pytest.raises(ImpersonationNotAllowedException):
        await use_case.execute(actor_admin_id=ADMIN_ID, target_user_id=ADMIN_ID)


@pytest.mark.asyncio
async def test_impersonating_another_privileged_user_is_refused(mock_uow):
    """No escalation: a target who may impersonate others is off limits."""
    mock_uow.users.get_or_raise = AsyncMock(return_value=MagicMock(is_active=True))
    mock_uow.users.ids_having_permission = AsyncMock(return_value={TARGET_ID})
    token_service = _token_service()

    use_case = ImpersonateUserUseCase(mock_uow, token_service)

    with pytest.raises(ImpersonationNotAllowedException):
        await use_case.execute(actor_admin_id=ADMIN_ID, target_user_id=TARGET_ID)

    mock_uow.users.ids_having_permission.assert_awaited_once_with(
        [TARGET_ID], Permissions.USER_IMPERSONATE
    )
    token_service.create_impersonation_token.assert_not_called()


@pytest.mark.asyncio
async def test_impersonating_deactivated_user_is_refused(mock_uow):
    mock_uow.users.get_or_raise = AsyncMock(return_value=MagicMock(is_active=False))
    token_service = _token_service()

    use_case = ImpersonateUserUseCase(mock_uow, token_service)

    with pytest.raises(AccountDeactivatedException):
        await use_case.execute(actor_admin_id=ADMIN_ID, target_user_id=TARGET_ID)

    token_service.create_impersonation_token.assert_not_called()


@pytest.mark.asyncio
async def test_impersonating_missing_user_propagates(mock_uow):
    mock_uow.users.get_or_raise = AsyncMock(side_effect=UserNotFoundException())
    token_service = _token_service()

    use_case = ImpersonateUserUseCase(mock_uow, token_service)

    with pytest.raises(UserNotFoundException):
        await use_case.execute(actor_admin_id=ADMIN_ID, target_user_id=TARGET_ID)

    token_service.create_impersonation_token.assert_not_called()
