import pytest

from app.infrastructure.security.password_hasher_impl import Argon2PasswordHasher


@pytest.fixture
def hasher():
    return Argon2PasswordHasher()


def test_hash_returns_string(hasher):
    hashed = hasher.hash("mysecret")

    assert isinstance(hashed, str)
    assert len(hashed) > 0


def test_verify_valid_password(hasher):
    password = "supersecret123"
    hashed = hasher.hash(password)

    assert hasher.verify(password, hashed) is True


def test_verify_invalid_password(hasher):
    hashed = hasher.hash("correct-password")

    assert hasher.verify("wrong-password", hashed) is False


def test_hash_is_not_deterministic(hasher):
    password = "same-password"

    hash1 = hasher.hash(password)
    hash2 = hasher.hash(password)

    assert hash1 != hash2


def test_hash_contains_argon2_signature(hasher):
    hashed = hasher.hash("test123")

    assert "$argon2" in hashed
