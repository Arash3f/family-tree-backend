from jose.exceptions import JWTError
import pytest
from jose import jwt

from app.core.config import setting
from app.infrastructure.security.jwt_service import JWTService


@pytest.fixture
def jwt_service():
    return JWTService()


def test_create_access_token(jwt_service):
    token = jwt_service.create_access_token(user_id=1)

    payload = jwt.decode(token, setting.JWT_SECRET, algorithms=[setting.JWT_ALGORITHM])

    assert payload["sub"] == "1"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_refresh_token(jwt_service):
    token = jwt_service.create_refresh_token(user_id=1)

    payload = jwt.decode(token, setting.JWT_SECRET, algorithms=[setting.JWT_ALGORITHM])

    assert payload["sub"] == "1"
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_decode_token(jwt_service):
    token = jwt_service.create_access_token(user_id=5)

    payload = jwt_service.decode_token(token)

    assert payload["sub"] == "5"
    assert payload["type"] == "access"


def test_decode_invalid_token(jwt_service):
    with pytest.raises(JWTError):
        jwt_service.decode_token("invalid.token.here")
