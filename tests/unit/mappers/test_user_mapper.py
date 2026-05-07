import pytest

from app.application.dto.user.user_create_dto import UserCreateMapper
from app.application.dto.user.user_get_dto import UserGetMapper
from app.application.dto.user.user_update_dto import UserUpdateMapper
from app.domain.entities.user import User


def create_user(**kwargs):
    data = {
        "id": 1,
        "username": "arash",
        "password_hash": "pass",
        "role_id": 2,
    }
    data.update(kwargs)
    return User(**data)


def test_user_create_mapper_to_response():
    user = create_user()

    dto = UserCreateMapper.to_response(user)

    assert dto.id == user.id
    assert dto.username == user.username
    assert dto.role_id == user.role_id


def test_user_get_mapper_to_response():
    user = create_user()

    dto = UserGetMapper.to_response(user)

    assert dto.id == user.id
    assert dto.username == user.username
    assert dto.role_id == user.role_id


def test_user_update_mapper_to_response():
    user = create_user()

    dto = UserUpdateMapper.to_response(user)

    assert dto.id == user.id
    assert dto.username == user.username
    assert dto.role_id == user.role_id


def test_user_mapper_raises_if_id_is_none():
    user = create_user(id=None)

    with pytest.raises(AssertionError):
        UserCreateMapper.to_response(user)
