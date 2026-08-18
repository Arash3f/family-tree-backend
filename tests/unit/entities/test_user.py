from unittest.mock import Mock
from uuid import UUID

import pytest

from app.domain.entities.user import User
from app.domain.exceptions.common_exceptions import UnExpectedIdException
from app.domain.services.password_hasher import PasswordHasher


def create_user(**overrides):
    return User(
        id=overrides.get("id", UUID(int=1)),
        role_id=overrides.get("role_id", UUID(int=2)),
        username=overrides.get("username", "arash"),
        password_hash=overrides.get("password_hash", "hashed_password"),
    )


def test_verify_password_success():
    user = create_user()

    hasher = Mock(spec=PasswordHasher)
    hasher.verify.return_value = True

    result = user.verify_password("plain_password", hasher)

    assert result is True
    hasher.verify.assert_called_once_with("plain_password", "hashed_password")


def test_verify_password_failure():
    user = create_user()

    hasher = Mock(spec=PasswordHasher)
    hasher.verify.return_value = False

    result = user.verify_password("wrong_password", hasher)

    assert result is False
    hasher.verify.assert_called_once_with("wrong_password", "hashed_password")


def test_safe_id_returns_id():
    user = create_user(id=UUID(int=10))

    assert user.safe_id == UUID(int=10)


def test_safe_id_raises_exception_when_id_none():
    user = create_user(id=None)

    with pytest.raises(UnExpectedIdException):
        _ = user.safe_id
