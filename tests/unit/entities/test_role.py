import pytest

from app.domain.entities.role import Role
from app.domain.exceptions.common_exceptions import UnExpectedIdException


def create_role(**overrides):
    return Role(
        id=overrides.get("id", 1),
        name=overrides.get("name", "admin"),
        permission_ids=overrides.get("permission_ids", [1, 2, 3]),
    )


def test_duplicate_permissions_are_removed_on_init():
    role = create_role(permission_ids=[1, 2, 2, 3, 1])

    assert role.permission_ids == [1, 2, 3]


def test_remove_duplicate_permission_method():
    role = create_role(permission_ids=[1, 1, 2, 3, 3])

    role.remove_duplicate_permission()

    assert role.permission_ids == [1, 2, 3]


def test_safe_id_returns_id():
    role = create_role(id=10)

    assert role.safe_id == 10


def test_safe_id_raises_exception_if_none():
    role = create_role(id=None)

    with pytest.raises(UnExpectedIdException):
        _ = role.safe_id
