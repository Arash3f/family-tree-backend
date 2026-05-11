from app.application.dto.permission.permission_create_dto import PermissionCreateMapper
from app.application.dto.permission.permission_get_dto import PermissionGetMapper
from app.domain.entities.permission import Permission


def create_permission(**overrides):
    return Permission(
        id=overrides.get("id", 1),
        name=overrides.get("name", "read_users"),
    )


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
