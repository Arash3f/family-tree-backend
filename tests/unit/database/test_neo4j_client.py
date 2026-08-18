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
