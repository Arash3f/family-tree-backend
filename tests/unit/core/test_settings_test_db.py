from typing import Any

import pytest
from pydantic import ValidationError

from app.core.config import AppSettings


def _base_kwargs(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "JWT_SECRET": "local-dev-only-change-me-32chars-min",
        "POSTGRES_HOST": "127.0.0.1",
        "POSTGRES_PORT": 5432,
        "POSTGRES_DB": "family_tree",
        "POSTGRES_HOST_TEST": "127.0.0.1",
        "POSTGRES_PORT_TEST": 5432,
        "POSTGRES_DB_TEST": "family_tree_test",
    }
    data.update(overrides)
    return data


def test_settings_accept_distinct_test_database():
    settings = AppSettings(_env_file=None, **_base_kwargs())  # type: ignore[call-arg]
    assert settings.POSTGRES_DB_TEST == "family_tree_test"
    assert settings.POSTGRES_DB != settings.POSTGRES_DB_TEST


def test_settings_reject_identical_app_and_test_database():
    with pytest.raises(ValidationError, match="POSTGRES_DB_TEST must target"):
        AppSettings(
            _env_file=None,  # type: ignore[call-arg]
            **_base_kwargs(POSTGRES_DB_TEST="family_tree"),
        )


def test_default_test_database_name_is_family_tree_test():
    field = AppSettings.model_fields["POSTGRES_DB_TEST"]
    assert field.default == "family_tree_test"


def test_settings_reject_weak_secrets_in_production():
    with pytest.raises(ValidationError, match="Weak/default secrets"):
        AppSettings(
            _env_file=None,  # type: ignore[call-arg]
            **_base_kwargs(ENVIRONMENT="production"),
        )


def test_settings_allow_weak_secrets_in_local():
    settings = AppSettings(
        _env_file=None,  # type: ignore[call-arg]
        **_base_kwargs(ENVIRONMENT="local", ADMIN_PASSWORD="admin"),
    )
    assert settings.ENVIRONMENT == "local"


def _strong_secret_kwargs(**overrides: Any) -> dict[str, Any]:
    return _base_kwargs(
        ADMIN_PASSWORD="Str0ng-Admin-Pass!",  # pragma: allowlist secret
        NEO4J_PASSWORD="Str0ng-Neo4j-Pass!",  # pragma: allowlist secret
        POSTGRES_PASSWORD="Str0ng-Postgres-Pass!",  # pragma: allowlist secret
        MINIO_ACCESS_KEY="not-minioadmin",  # pragma: allowlist secret
        MINIO_SECRET_KEY="not-minioadmin",  # pragma: allowlist secret
        JWT_SECRET="a-real-production-secret-that-is-long-enough",
        **overrides,
    )


def test_settings_reject_wildcard_cors_origin_outside_local():
    with pytest.raises(ValidationError, match="Weak/default secrets"):
        AppSettings(
            _env_file=None,  # type: ignore[call-arg]
            **_strong_secret_kwargs(ENVIRONMENT="production", CORS_ORIGINS="*"),
        )


def test_settings_allow_wildcard_cors_origin_in_local():
    settings = AppSettings(
        _env_file=None,  # type: ignore[call-arg]
        **_base_kwargs(ENVIRONMENT="local", CORS_ORIGINS="*"),
    )
    assert settings.CORS_ORIGINS == "*"
