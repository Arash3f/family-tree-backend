from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from app.presentation.rest.dependencies import rate_limit as rate_limit_module
from app.presentation.rest.dependencies.rate_limit import rate_limit_auth


def _request(host: str | None) -> Request:
    request = MagicMock(spec=Request)
    if host is None:
        request.client = None
    else:
        request.client = SimpleNamespace(host=host)
    return request


@pytest.fixture
def redis_mock():
    client = MagicMock()
    pipe = MagicMock()
    # default: first two calls succeed (count grows), third exceeds
    pipe.execute = AsyncMock(
        side_effect=[
            (0, 1, 1, True),
            (0, 1, 2, True),
            (0, 1, 3, True),
        ]
    )
    client.pipeline.return_value = pipe
    with patch.object(rate_limit_module, "get_rate_limit_redis", return_value=client):
        yield client, pipe


@pytest.fixture
def broken_redis():
    client = MagicMock()
    client.pipeline.side_effect = rate_limit_module.redis.RedisError("down")
    with patch.object(rate_limit_module, "get_rate_limit_redis", return_value=client):
        yield client


@pytest.mark.asyncio
async def test_rate_limit_disabled(redis_mock):
    request = _request("1.1.1.1")
    with patch.object(rate_limit_module.settings, "AUTH_RATE_LIMIT_PER_MINUTE", 0):
        await rate_limit_auth(request)
    redis_mock[0].pipeline.assert_not_called()


@pytest.mark.asyncio
async def test_rate_limit_allows_then_blocks(redis_mock):
    request = _request("2.2.2.2")
    with patch.object(rate_limit_module.settings, "AUTH_RATE_LIMIT_PER_MINUTE", 2):
        await rate_limit_auth(request)
        await rate_limit_auth(request)
        with pytest.raises(HTTPException) as exc:
            await rate_limit_auth(request)
        assert exc.value.status_code == 429


@pytest.mark.asyncio
async def test_rate_limit_unknown_client(redis_mock):
    request = _request(None)
    pipe = redis_mock[1]
    pipe.execute = AsyncMock(side_effect=[(0, 1, 1, True)])
    with patch.object(rate_limit_module.settings, "AUTH_RATE_LIMIT_PER_MINUTE", 5):
        await rate_limit_auth(request)
    # Key is derived from "unknown" IP label
    args = pipe.zadd.call_args
    assert args is not None


@pytest.mark.asyncio
async def test_rate_limit_stays_open_locally_when_redis_is_down(broken_redis):
    """A developer without Redis running should still be able to log in."""
    request = _request("3.3.3.3")
    with (
        patch.object(rate_limit_module.settings, "ENVIRONMENT", "local"),
        patch.object(rate_limit_module.settings, "AUTH_RATE_LIMIT_PER_MINUTE", 1),
    ):
        await rate_limit_auth(request)


@pytest.mark.asyncio
async def test_rate_limit_fails_closed_in_production_when_redis_is_down(broken_redis):
    """With no counter available, unlimited login attempts is the worse outcome."""
    request = _request("3.3.3.3")
    with (
        patch.object(rate_limit_module.settings, "ENVIRONMENT", "production"),
        patch.object(rate_limit_module.settings, "AUTH_RATE_LIMIT_PER_MINUTE", 1),
        pytest.raises(HTTPException) as exc,
    ):
        await rate_limit_auth(request)

    assert exc.value.status_code == 503
