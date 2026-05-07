import pytest
from app.application.dto.permission.permission_create_dto import PermissionCreateMapper
from app.application.dto.permission.permission_get_dto import PermissionGetMapper
from app.domain.entities.permission import Permission


def create_permission(**kwargs):
    data = {
        "id": 1,
        "name": "read_users",
    }
    data.update(kwargs)
    return Permission(**data)


def test_permission_create_mapper_to_response():
    permission = create_permission()

    dto = PermissionCreateMapper.to_response(permission)

    assert dto.id == permission.id
    assert dto.name == permission.name


def test_permission_get_mapper_to_response():
    permission = create_permission()

    dto = PermissionGetMapper.to_response(permission)

    assert dto.id == permission.id
    assert dto.name == permission.name


def test_permission_mapper_raises_if_id_is_none():
    permission = create_permission(id=None)

    with pytest.raises(AssertionError):
        PermissionCreateMapper.to_response(permission)
