import importlib

import pytest

from app.core.config import settings

SCHEMA_MODULE = "app.presentation.graphql.schema"

INTROSPECTION_QUERY = "{ __schema { types { name } } }"


def _reload_schema(monkeypatch: pytest.MonkeyPatch, environment: str):
    """Rebuild the schema module under a given ENVIRONMENT.

    The extension list is assembled at import time, so the module has to be
    reloaded to observe a different environment.
    """
    monkeypatch.setattr(settings, "ENVIRONMENT", environment)
    module = importlib.import_module(SCHEMA_MODULE)
    return importlib.reload(module)


@pytest.fixture(autouse=True)
def restore_schema_module():
    yield
    # Leave the imported module matching the real environment for other tests.
    importlib.reload(importlib.import_module(SCHEMA_MODULE))


@pytest.mark.asyncio
async def test_introspection_is_available_locally(monkeypatch: pytest.MonkeyPatch):
    module = _reload_schema(monkeypatch, "local")

    result = await module.schema.execute(INTROSPECTION_QUERY)

    assert result.errors is None


@pytest.mark.asyncio
async def test_introspection_is_blocked_in_production(monkeypatch: pytest.MonkeyPatch):
    """Schema dumps hand an attacker the full attack surface for free."""
    module = _reload_schema(monkeypatch, "production")

    result = await module.schema.execute(INTROSPECTION_QUERY)

    assert result.errors
    assert "introspection" in str(result.errors[0]).lower()


def test_graphiql_is_disabled_outside_development(monkeypatch: pytest.MonkeyPatch):
    module = _reload_schema(monkeypatch, "production")

    assert module.graphql_router.graphql_ide is None


def test_graphiql_is_served_locally(monkeypatch: pytest.MonkeyPatch):
    module = _reload_schema(monkeypatch, "local")

    assert module.graphql_router.graphql_ide == "graphiql"


@pytest.mark.asyncio
async def test_deeply_nested_query_is_rejected(monkeypatch: pytest.MonkeyPatch):
    module = _reload_schema(monkeypatch, "local")
    depth = settings.GRAPHQL_MAX_DEPTH + 2
    query = "{ " + "me { " * depth + "id" + " }" * depth + " }"

    result = await module.schema.execute(query)

    assert result.errors
    assert "depth" in str(result.errors[0]).lower()


@pytest.mark.asyncio
async def test_alias_flood_is_rejected(monkeypatch: pytest.MonkeyPatch):
    """Aliases multiply the work of one document without deepening it."""
    module = _reload_schema(monkeypatch, "local")
    count = settings.GRAPHQL_MAX_ALIASES + 5
    aliases = " ".join(f"a{i}: me {{ id }}" for i in range(count))

    result = await module.schema.execute("{ " + aliases + " }")

    assert result.errors
    assert "alias" in str(result.errors[0]).lower()


@pytest.mark.asyncio
async def test_oversized_document_is_rejected(monkeypatch: pytest.MonkeyPatch):
    module = _reload_schema(monkeypatch, "local")
    query = "{ " + " ".join(["me { id }"] * settings.GRAPHQL_MAX_TOKENS) + " }"

    result = await module.schema.execute(query)

    assert result.errors
    assert "token" in str(result.errors[0]).lower()
