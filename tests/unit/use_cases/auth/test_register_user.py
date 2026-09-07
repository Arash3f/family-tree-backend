from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.application.dto.auth_dto import RegisterDTO
from app.application.use_cases.auth.register_user import (
    RegisterUserUseCase,
    normalize_register_email,
    normalize_register_phone,
)
from app.core.config import settings
from app.domain.exceptions.user_exceptions import (
    EmailAlreadyExistsException,
    PasswordConfirmationMismatchException,
    UsernameAlreadyExistsException,
)
from app.domain.shared.account_type import AccountType
from app.domain.shared.starter_trees import STARTER_TREE_SPECS


def test_normalize_register_email_lowercases():
    assert normalize_register_email("  Ada@Example.COM ") == "ada@example.com"
    assert normalize_register_email("  ") is None
    assert normalize_register_email(None) is None


def test_normalize_register_phone_combines_country_code():
    assert normalize_register_phone("0912 345 6789", "+98") == "+989123456789"
    assert normalize_register_phone("9123456789", "98") == "+989123456789"
    assert normalize_register_phone("9123456789", None) == "9123456789"
    assert normalize_register_phone("  ", "+98") is None


@pytest.mark.asyncio
async def test_register_creates_free_member_and_returns_tokens(mock_uow):
    role = MagicMock()
    role.safe_id = UUID(int=7)
    created_user = MagicMock()
    created_user.safe_id = UUID(int=42)

    mock_uow.users.get_by_username = AsyncMock(return_value=None)
    mock_uow.users.get_by_email = AsyncMock(return_value=None)
    mock_uow.roles.get_by_name = AsyncMock(return_value=role)
    mock_uow.users.create = AsyncMock(return_value=created_user)
    mock_uow.sessions.create = AsyncMock()
    mock_uow.commit = AsyncMock()

    created_trees = []
    for i, spec in enumerate(STARTER_TREE_SPECS, start=1):
        tree = MagicMock()
        tree.safe_id = UUID(int=100 + i)
        tree.name = spec.default_name
        created_trees.append(tree)

    mock_uow.family_trees.create = AsyncMock(side_effect=created_trees)
    mock_uow.tree_memberships.create = AsyncMock()

    password_hasher = MagicMock()
    password_hasher.hash.return_value = "hashed"
    token_service = MagicMock()
    token_service.create_access_token.return_value = "access"
    token_service.create_refresh_token.return_value = "refresh"
    token_service.hash_token.return_value = "refresh-hash"

    usecase = RegisterUserUseCase(mock_uow, password_hasher, token_service)
    result = await usecase.execute(
        RegisterDTO(
            username="newuser",
            password="secret123",
            re_password="secret123",
            email="New@Example.com",
            phone="9123456789",
            country_code="+98",
        ),
        user_agent="test-agent",
        ip_address="127.0.0.1",
    )

    assert result.access_token == "access"
    assert result.refresh_token == "refresh"
    mock_uow.roles.get_by_name.assert_awaited_once_with(settings.MEMBER_ROLE_NAME)

    created = mock_uow.users.create.await_args.args[0]
    assert created.username == "newuser"
    assert created.email == "new@example.com"
    assert created.phone == "+989123456789"
    assert created.role_id == UUID(int=7)
    assert created.account_type is AccountType.FREE
    assert created.password_hash == "hashed"

    assert mock_uow.family_trees.create.await_count == len(STARTER_TREE_SPECS)
    tree_names = [
        call.args[0].name for call in mock_uow.family_trees.create.await_args_list
    ]
    assert tree_names == [spec.default_name for spec in STARTER_TREE_SPECS]
    assert mock_uow.tree_memberships.create.await_count == len(STARTER_TREE_SPECS)

    mock_uow.sessions.create.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_rejects_password_mismatch(mock_uow):
    usecase = RegisterUserUseCase(mock_uow, MagicMock(), MagicMock())
    with pytest.raises(PasswordConfirmationMismatchException):
        await usecase.execute(
            RegisterDTO(
                username="newuser",
                password="secret123",
                re_password="other123",
            )
        )


@pytest.mark.asyncio
async def test_register_rejects_duplicate_username(mock_uow):
    mock_uow.users.get_by_username = AsyncMock(return_value=MagicMock())
    usecase = RegisterUserUseCase(mock_uow, MagicMock(), MagicMock())
    with pytest.raises(UsernameAlreadyExistsException):
        await usecase.execute(
            RegisterDTO(
                username="taken",
                password="secret123",
                re_password="secret123",
            )
        )


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email(mock_uow):
    mock_uow.users.get_by_username = AsyncMock(return_value=None)
    mock_uow.users.get_by_email = AsyncMock(return_value=MagicMock())
    usecase = RegisterUserUseCase(mock_uow, MagicMock(), MagicMock())
    with pytest.raises(EmailAlreadyExistsException):
        await usecase.execute(
            RegisterDTO(
                username="newuser",
                password="secret123",
                re_password="secret123",
                email="used@example.com",
            )
        )
