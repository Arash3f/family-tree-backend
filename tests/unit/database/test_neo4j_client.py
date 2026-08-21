import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.infrastructure.database.neo4j.neo4j import Neo4jClient, _LazyNeo4jClient


@pytest.mark.asyncio
async def test_concurrent_first_access_builds_only_one_client():
    """Two coroutines racing on the very first attribute access must not
    each construct their own Neo4jClient -- the loser's driver would never
    be closed, leaking a connection pool."""
    lazy = _LazyNeo4jClient()

    created = []

    async def fake_create():
        # Yield control so a second _get() call can interleave here if the
        # lock isn't actually preventing it.
        await asyncio.sleep(0)
        client = AsyncMock(spec=Neo4jClient)
        created.append(client)
        return client

    with patch.object(Neo4jClient, "create", side_effect=fake_create):
        first, second = await asyncio.gather(lazy._get(), lazy._get())

    assert first is second
    assert len(created) == 1


@pytest.mark.asyncio
async def test_get_reuses_already_constructed_client():
    lazy = _LazyNeo4jClient()
    existing = AsyncMock(spec=Neo4jClient)
    lazy._client = existing

    with patch.object(Neo4jClient, "create") as create_mock:
        result = await lazy._get()

    assert result is existing
    create_mock.assert_not_called()


@pytest.mark.asyncio
async def test_close_clears_client_and_lock():
    lazy = _LazyNeo4jClient()
    existing = AsyncMock(spec=Neo4jClient)
    lazy._client = existing
    lazy._init_lock = asyncio.Lock()

    await lazy.close()

    assert lazy._client is None
    assert lazy._init_lock is None
    existing.close.assert_awaited_once()


def test_run_celery_coro_closes_client_after_success():
    from app.infrastructure.database.neo4j import neo4j as neo4j_mod

    async def ok():
        return 42

    with patch.object(
        neo4j_mod.neo4j_client, "close", new_callable=AsyncMock
    ) as close_mock:
        assert neo4j_mod.run_celery_coro(ok()) == 42
        close_mock.assert_awaited_once()


def test_run_celery_coro_closes_client_after_failure():
    from app.infrastructure.database.neo4j import neo4j as neo4j_mod

    async def boom():
        raise ValueError("nope")

    with patch.object(
        neo4j_mod.neo4j_client, "close", new_callable=AsyncMock
    ) as close_mock:
        with pytest.raises(ValueError, match="nope"):
            neo4j_mod.run_celery_coro(boom())
        close_mock.assert_awaited_once()
