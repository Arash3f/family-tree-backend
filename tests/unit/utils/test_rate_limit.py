from types import SimpleNamespace
from unittest.mock import MagicMock, patch

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
    pipe.execute.side_effect = [
        (0, 1, 1, True),
        (0, 1, 2, True),
        (0, 1, 3, True),
    ]
    client.pipeline.return_value = pipe
    with patch.object(rate_limit_module, "get_rate_limit_redis", return_value=client):
        yield client, pipe


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
    pipe.execute.side_effect = [(0, 1, 1, True)]
    with patch.object(rate_limit_module.settings, "AUTH_RATE_LIMIT_PER_MINUTE", 5):
        await rate_limit_auth(request)
    # Key is derived from "unknown" IP label
    args = pipe.zadd.call_args
    assert args is not None


@pytest.mark.asyncio
async def test_rate_limit_fails_open_on_redis_error():
    client = MagicMock()
    client.pipeline.side_effect = rate_limit_module.redis.RedisError("down")
    request = _request("3.3.3.3")
    with (
        patch.object(rate_limit_module, "get_rate_limit_redis", return_value=client),
        patch.object(rate_limit_module.settings, "AUTH_RATE_LIMIT_PER_MINUTE", 1),
    ):
        await rate_limit_auth(request)
