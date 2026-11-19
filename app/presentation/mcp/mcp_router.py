from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response

from app.core.config import settings
from app.domain.entities.user import User
from app.domain.exceptions.mcp_exceptions import McpDisabledException
from app.presentation.mcp.auth import require_mcp_user
from app.presentation.mcp.protocol import SERVER_INFO, handle_jsonrpc, list_tool_names

router = APIRouter(tags=["MCP"], include_in_schema=False)


@router.get("/mcp")
async def mcp_get_info() -> JSONResponse:
    """Discovery helper for humans; agents use POST JSON-RPC."""
    if not settings.MCP_ENABLED:
        raise McpDisabledException()
    return JSONResponse(
        {
            "server": SERVER_INFO,
            "transport": "streamable-http-json",
            "auth": "Bearer ftmcp_… personal access token",
            "tools": list_tool_names(),
            "endpoint": settings.mcp_public_url or "/mcp",
        }
    )


@router.post("/mcp")
async def mcp_post(
    request: Request,
    _user: User = Depends(require_mcp_user),
) -> Response:
    """JSON-RPC MCP endpoint (initialize / tools/list / tools/call)."""
    if not settings.MCP_ENABLED:
        raise McpDisabledException()

    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        return JSONResponse(
            {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
            status_code=400,
        )

    # Batch support (array of messages) — return an array of responses.
    if isinstance(payload, list):
        responses: list[dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, dict):
                responses.append(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32600, "message": "Invalid Request"},
                    }
                )
                continue
            result = await handle_jsonrpc(item)
            if result is not None:
                responses.append(result)
        if not responses:
            return Response(status_code=202)
        return JSONResponse(responses)

    if not isinstance(payload, dict):
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "Invalid Request"},
            },
            status_code=400,
        )

    result = await handle_jsonrpc(payload)
    if result is None:
        return Response(status_code=202)
    return JSONResponse(result)
