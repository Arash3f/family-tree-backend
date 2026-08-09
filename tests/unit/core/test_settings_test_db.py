import pytest
from pydantic import ValidationError

from app.core.config import AppSettings


def _base_kwargs(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
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
            _env_file=None,
            **_base_kwargs(POSTGRES_DB_TEST="family_tree"),  # type: ignore[arg-type]
        )


def test_default_test_database_name_is_family_tree_test():
    field = AppSettings.model_fields["POSTGRES_DB_TEST"]
    assert field.default == "family_tree_test"
