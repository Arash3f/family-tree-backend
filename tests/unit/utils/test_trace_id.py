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
