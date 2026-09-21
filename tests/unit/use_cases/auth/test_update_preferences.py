from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from app.application.dto.session_dto import UpdatePreferencesDTO
from app.application.use_cases.auth.me_and_password import UpdateOwnPreferencesUseCase
from app.domain.entities.user import User
from app.domain.shared.user_preferences import PreferredLocale, PreferredTheme


@pytest.mark.asyncio
async def test_update_own_preferences_sets_locale_and_theme(mock_uow):
    user = User(
        id=UUID(int=1),
        username="tester",
        password_hash="hash",
    )
    mock_uow.users.get_or_raise.return_value = user
    mock_uow.users.update = AsyncMock(return_value=user)

    usecase = UpdateOwnPreferencesUseCase(mock_uow)
    result = await usecase.execute(
        user.safe_id,
        UpdatePreferencesDTO(preferred_locale="fa", preferred_theme="dark"),
    )

    assert result.result == "Preferences updated"
    assert user.preferred_locale is PreferredLocale.FA
    assert user.preferred_theme is PreferredTheme.DARK
    mock_uow.users.update.assert_awaited_once_with(user)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_own_preferences_partial_locale_only(mock_uow):
    user = User(
        id=UUID(int=1),
        username="tester",
        password_hash="hash",
        preferred_theme=PreferredTheme.SYSTEM,
    )
    mock_uow.users.get_or_raise.return_value = user
    mock_uow.users.update = AsyncMock(return_value=user)

    usecase = UpdateOwnPreferencesUseCase(mock_uow)
    await usecase.execute(
        user.safe_id,
        UpdatePreferencesDTO.model_validate({"preferred_locale": "en"}),
    )

    assert user.preferred_locale is PreferredLocale.EN
    assert user.preferred_theme is PreferredTheme.SYSTEM
