import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.main import health


def _uow_mock(*, fail_execute: bool = False) -> MagicMock:
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=False)
    if fail_execute:
        uow.session.execute = AsyncMock(side_effect=RuntimeError("postgres down"))
    else:
        uow.session.execute = AsyncMock(return_value=None)
    return uow


@pytest.mark.asyncio
async def test_health_ok_returns_200():
    with (
        patch("app.main.get_uow", return_value=_uow_mock()),
        patch("app.main.neo4j_client") as neo4j,
    ):
        neo4j.execute_read.return_value = [{"ok": 1}]
        response = await health()

    assert response.status_code == 200
    data = json.loads(response.body)
    assert data["status"] == "ok"
    assert data["postgres"] == "ok"
    assert data["neo4j"] == "ok"


@pytest.mark.asyncio
async def test_health_degraded_returns_503_when_postgres_fails():
    with (
        patch("app.main.get_uow", return_value=_uow_mock(fail_execute=True)),
        patch("app.main.neo4j_client") as neo4j,
    ):
        neo4j.execute_read.return_value = [{"ok": 1}]
        response = await health()

    assert response.status_code == 503
    data = json.loads(response.body)
    assert data["status"] == "degraded"
    assert data["postgres"] == "error"
    assert data["neo4j"] == "ok"


@pytest.mark.asyncio
async def test_health_degraded_returns_503_when_neo4j_fails():
    with (
        patch("app.main.get_uow", return_value=_uow_mock()),
        patch("app.main.neo4j_client") as neo4j,
    ):
        neo4j.execute_read.side_effect = RuntimeError("neo4j down")
        response = await health()

    assert response.status_code == 503
    data = json.loads(response.body)
    assert data["status"] == "degraded"
    assert data["postgres"] == "ok"
    assert data["neo4j"] == "error"
