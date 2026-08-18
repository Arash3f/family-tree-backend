from uuid import UUID

from app.application.dto.user.user_create_dto import UserCreateMapper
from app.application.dto.user.user_get_dto import UserGetMapper
from app.application.dto.user.user_update_dto import UserUpdateMapper
from app.domain.entities.user import User


def create_user(**overrides):
    return User(
        id=overrides.get("id", UUID(int=1)),
        username=overrides.get("username", "arash"),
        fullname=overrides.get("fullname", "Arash"),
        password_hash=overrides.get("password_hash", "pass"),
        role_id=overrides.get("role_id"),
    )


def test_user_create_mapper_to_response():
    user = create_user()

    dto = UserCreateMapper.to_response(user)

    assert dto.id == user.id
    assert dto.username == user.username
    assert dto.fullname == user.fullname
    assert dto.role_id == user.role_id
    assert dto.account_type == user.account_type


def test_user_get_mapper_to_response():
    user = create_user()

    dto = UserGetMapper.to_response(user)

    assert dto.id == user.id
    assert dto.username == user.username
    assert dto.fullname == user.fullname
    assert dto.role_id == user.role_id
    assert dto.account_type == user.account_type


def test_user_update_mapper_to_response():
    user = create_user()

    dto = UserUpdateMapper.to_response(user)

    assert dto.id == user.id
    assert dto.username == user.username
    assert dto.fullname == user.fullname
    assert dto.role_id == user.role_id
    assert dto.account_type == user.account_type
