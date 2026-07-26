from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.presentation.rest.dependencies import rate_limit as rate_limit_module
from app.presentation.rest.dependencies.rate_limit import rate_limit_auth


@pytest.fixture(autouse=True)
def clear_attempts():
    rate_limit_module._attempts.clear()
    yield
    rate_limit_module._attempts.clear()


@pytest.mark.asyncio
async def test_rate_limit_disabled():
    request = SimpleNamespace(client=SimpleNamespace(host="1.1.1.1"))
    with patch.object(rate_limit_module.settings, "AUTH_RATE_LIMIT_PER_MINUTE", 0):
        assert await rate_limit_auth(request) is None


@pytest.mark.asyncio
async def test_rate_limit_allows_then_blocks():
    request = SimpleNamespace(client=SimpleNamespace(host="2.2.2.2"))
    with patch.object(rate_limit_module.settings, "AUTH_RATE_LIMIT_PER_MINUTE", 2):
        await rate_limit_auth(request)
        await rate_limit_auth(request)
        with pytest.raises(HTTPException) as exc:
            await rate_limit_auth(request)
        assert exc.value.status_code == 429


@pytest.mark.asyncio
async def test_rate_limit_unknown_client():
    request = SimpleNamespace(client=None)
    with patch.object(rate_limit_module.settings, "AUTH_RATE_LIMIT_PER_MINUTE", 1):
        await rate_limit_auth(request)
        assert "unknown" in rate_limit_module._attempts
