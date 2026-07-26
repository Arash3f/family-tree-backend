from uuid import UUID
import pytest

from app.domain.entities.permission import Permission
from app.domain.exceptions.common_exceptions import UnExpectedIdException


def test_safe_id_returns_id_when_present():
    permission = Permission(id=UUID(int=1), name="user:create")

    assert permission.safe_id == UUID(int=1)


def test_safe_id_raises_exception_when_id_is_none():
    permission = Permission(id=None, name="user:create")

    with pytest.raises(UnExpectedIdException):
        _ = permission.safe_id
