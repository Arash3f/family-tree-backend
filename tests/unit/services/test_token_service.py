from uuid import UUID
import pytest
from jose import jwt
from jose.exceptions import JWTError

from app.core.config import settings
from app.infrastructure.services.security.token_service_imp import JWTService


@pytest.fixture
def token_service():
    return JWTService()


def test_create_access_token(token_service):
    session_id = UUID(int=9)
    token = token_service.create_access_token(
        user_id=UUID(int=1), session_id=session_id
    )

    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )

    assert payload["sub"] == str(UUID(int=1))
    assert payload["sid"] == str(session_id)
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_refresh_token(token_service):
    session_id = UUID(int=9)
    token = token_service.create_refresh_token(
        user_id=UUID(int=1), session_id=session_id
    )

    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )

    assert payload["sub"] == str(UUID(int=1))
    assert payload["sid"] == str(session_id)
    assert payload["jti"] == str(session_id)
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_decode_token(token_service):
    token = token_service.create_access_token(
        user_id=UUID(int=5), session_id=UUID(int=2)
    )

    payload = token_service.decode_token(token)

    assert payload["sub"] == str(UUID(int=5))
    assert payload["type"] == "access"


def test_hash_token_is_stable(token_service):
    assert token_service.hash_token("abc") == token_service.hash_token("abc")
    assert token_service.hash_token("abc") != token_service.hash_token("abd")


def test_decode_invalid_token(token_service):
    with pytest.raises(JWTError):
        token_service.decode_token("invalid.token.here")
