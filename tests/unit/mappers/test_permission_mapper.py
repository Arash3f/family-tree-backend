from uuid import UUID

from app.application.dto.permission.permission_create_dto import PermissionCreateMapper
from app.application.dto.permission.permission_get_dto import PermissionGetMapper
from app.domain.entities.permission import Permission


def create_permission(**overrides):
    return Permission(
        id=overrides.get("id", UUID(int=1)),
        name=overrides.get("name", "read_users"),
        description_en=overrides.get("description_en", ""),
        description_fa=overrides.get("description_fa", ""),
    )


def test_permission_create_mapper_to_response():
    permission = create_permission(
        description_en="Create things",
        description_fa="ایجاد موارد",
    )

    dto = PermissionCreateMapper.to_response(permission)

    assert dto.id == permission.id
    assert dto.name == permission.name
    assert dto.description_en == "Create things"
    assert dto.description_fa == "ایجاد موارد"


def test_permission_get_mapper_to_response():
    permission = create_permission(
        description_en="Read things",
        description_fa="خواندن موارد",
    )

    dto = PermissionGetMapper.to_response(permission)

    assert dto.id == permission.id
    assert dto.name == permission.name
    assert dto.description_en == "Read things"
    assert dto.description_fa == "خواندن موارد"
