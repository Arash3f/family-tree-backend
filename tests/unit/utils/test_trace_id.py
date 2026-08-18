import pytest
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from app.presentation.rest.utils.trace_id import TraceIDMiddleware


async def homepage(request):
    return PlainTextResponse("ok")


@pytest.mark.asyncio
async def test_trace_id_middleware_generates_and_echoes():
    app = Starlette(routes=[Route("/", homepage)])
    app.add_middleware(TraceIDMiddleware)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.headers.get("X-Trace-ID")

        response2 = await client.get("/", headers={"X-Trace-ID": "fixed-trace"})
        assert response2.headers.get("X-Trace-ID") == "fixed-trace"


@pytest.mark.asyncio
async def test_trace_id_middleware_rejects_unsafe_client_value():
    """A crafted header must not reach logs verbatim (log-injection risk)."""
    app = Starlette(routes=[Route("/", homepage)])
    app.add_middleware(TraceIDMiddleware)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/", headers={"X-Trace-ID": "evil\r\nInjected-Header: 1"}
        )
        echoed = response.headers.get("X-Trace-ID")
        assert echoed != "evil\r\nInjected-Header: 1"
        assert "\r" not in echoed and "\n" not in echoed
