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


@pytest.fixture(autouse=True)
def clear_attempts():
    rate_limit_module._attempts.clear()
    yield
    rate_limit_module._attempts.clear()


@pytest.mark.asyncio
async def test_rate_limit_disabled():
    request = _request("1.1.1.1")
    with patch.object(rate_limit_module.settings, "AUTH_RATE_LIMIT_PER_MINUTE", 0):
        await rate_limit_auth(request)


@pytest.mark.asyncio
async def test_rate_limit_allows_then_blocks():
    request = _request("2.2.2.2")
    with patch.object(rate_limit_module.settings, "AUTH_RATE_LIMIT_PER_MINUTE", 2):
        await rate_limit_auth(request)
        await rate_limit_auth(request)
        with pytest.raises(HTTPException) as exc:
            await rate_limit_auth(request)
        assert exc.value.status_code == 429


@pytest.mark.asyncio
async def test_rate_limit_unknown_client():
    request = _request(None)
    with patch.object(rate_limit_module.settings, "AUTH_RATE_LIMIT_PER_MINUTE", 1):
        await rate_limit_auth(request)
        assert "unknown" in rate_limit_module._attempts
