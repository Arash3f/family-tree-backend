import pytest

from app.application.dto.role.role_create_dto import RoleCreateMapper
from app.application.dto.role.role_get_dto import RoleGetMapper
from app.application.dto.role.role_update_dto import RoleUpdateMapper
from app.domain.entities.role import Role


def create_role(**kwargs):
    data = {
        "id": 1,
        "name": "admin",
        "permission_ids": [1, 2, 3],
    }
    data.update(kwargs)
    return Role(**data)


def test_role_create_mapper_to_response():
    role = create_role()

    dto = RoleCreateMapper.to_response(role)

    assert dto.id == role.id
    assert dto.name == role.name
    assert dto.permission_ids == role.permission_ids


def test_role_get_mapper_to_response():
    role = create_role()

    dto = RoleGetMapper.to_response(role)

    assert dto.id == role.id
    assert dto.name == role.name
    assert dto.permission_ids == role.permission_ids


def test_role_update_mapper_to_response():
    role = create_role()

    dto = RoleUpdateMapper.to_response(role)

    assert dto.id == role.id
    assert dto.name == role.name


def test_role_mapper_raises_if_id_is_none():
    role = create_role(id=None)

    with pytest.raises(AssertionError):
        RoleCreateMapper.to_response(role)
