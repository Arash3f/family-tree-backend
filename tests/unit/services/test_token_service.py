import pytest
from jose import jwt
from jose.exceptions import JWTError

from app.core.config import settings
from app.infrastructure.services.security.token_service_imp import JWTService


@pytest.fixture
def token_service():
    return JWTService()


def test_create_access_token(token_service):
    token = token_service.create_access_token(user_id=1)

    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )

    assert payload["sub"] == "1"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_refresh_token(token_service):
    token = token_service.create_refresh_token(user_id=1)

    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )

    assert payload["sub"] == "1"
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_decode_token(token_service):
    token = token_service.create_access_token(user_id=5)

    payload = token_service.decode_token(token)

    assert payload["sub"] == "5"
    assert payload["type"] == "access"


def test_decode_invalid_token(token_service):
    with pytest.raises(JWTError):
        token_service.decode_token("invalid.token.here")
