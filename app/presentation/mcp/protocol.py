"""Minimal Streamable-HTTP MCP (JSON-RPC) for Family Tree tools.

Speaks enough of the MCP surface that Claude / Cursor / other agents can
discover and call tools over ``POST /mcp`` with a Bearer personal token.
Kept deliberately smaller than a full SDK mount: no sessions, JSON only.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable
from uuid import uuid4

ProtocolHandler = Callable[..., Awaitable[str]]

SERVER_INFO = {
    "name": "family-tree",
    "version": "1.0.0",
    "title": "Family Tree MCP",
}

INSTRUCTIONS = (
    "Read-only tools over the caller's family trees. "
    "Prefer list_trees first, then search_persons / get_person / "
    "get_person_card / get_relationship. Every tree-scoped tool needs tree_id."
)

TOOL_DEFS: list[dict[str, Any]] = [
    {
        "name": "whoami",
        "description": "Return the authenticated user (id, username, fullname, account).",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "list_trees",
        "description": "List family trees the caller can access.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "search_persons",
        "description": "Search people in a tree by name (partial match).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tree_id": {"type": "string", "description": "Family tree UUID"},
                "name": {"type": "string", "description": "Name fragment to search"},
                "page": {"type": "integer", "minimum": 1, "default": 1},
                "page_size": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 20,
                },
            },
            "required": ["tree_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_person",
        "description": "Fetch one person by id inside a tree.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tree_id": {"type": "string"},
                "person_id": {"type": "string"},
            },
            "required": ["tree_id", "person_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_person_card",
        "description": "Pedigree card: parents, spouses and children for one person.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tree_id": {"type": "string"},
                "person_id": {"type": "string"},
            },
            "required": ["tree_id", "person_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_relationship",
        "description": "Closest kinship path between two people in a tree.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tree_id": {"type": "string"},
                "from_person_id": {"type": "string"},
                "to_person_id": {"type": "string"},
                "male_only": {
                    "type": "boolean",
                    "default": False,
                    "description": "Prefer paternal-line paths when true",
                },
            },
            "required": ["tree_id", "from_person_id", "to_person_id"],
            "additionalProperties": False,
        },
    },
]

def _handlers() -> dict[str, ProtocolHandler]:
    # Lazy import so protocol unit tests (and OpenAPI boot) do not pull MinIO/PIL
    # until a tool is actually called.
    from app.presentation.mcp import tools as mcp_tools

    return {
        "whoami": mcp_tools.tool_whoami,
        "list_trees": mcp_tools.tool_list_trees,
        "search_persons": mcp_tools.tool_search_persons,
        "get_person": mcp_tools.tool_get_person,
        "get_person_card": mcp_tools.tool_get_person_card,
        "get_relationship": mcp_tools.tool_get_relationship,
    }


def list_tool_names() -> list[str]:
    return [tool["name"] for tool in TOOL_DEFS]


async def dispatch_tool(name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
    handler = _handlers().get(name)
    if handler is None:
        return {
            "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
            "isError": True,
        }
    args = arguments or {}
    try:
        text = await handler(**args)
    except TypeError as exc:
        return {
            "content": [{"type": "text", "text": f"Invalid arguments: {exc}"}],
            "isError": True,
        }
    except Exception as exc:  # noqa: BLE001 — surface to the agent, don't 500 the RPC
        return {
            "content": [{"type": "text", "text": f"Tool failed: {exc}"}],
            "isError": True,
        }
    return {"content": [{"type": "text", "text": text}], "isError": False}


def _rpc_result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _rpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


async def handle_jsonrpc(message: dict[str, Any]) -> dict[str, Any] | None:
    """Handle one JSON-RPC MCP message. Notifications return None (no body)."""
    if message.get("jsonrpc") != "2.0":
        return _rpc_error(message.get("id"), -32600, "Invalid Request")

    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}

    # Notifications have no id — acknowledge by returning no payload.
    if request_id is None and isinstance(method, str) and method.startswith("notifications/"):
        return None

    if method == "initialize":
        client_version = (
            params.get("protocolVersion") if isinstance(params, dict) else None
        )
        return _rpc_result(
            request_id,
            {
                "protocolVersion": client_version or "2025-03-26",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
                "instructions": INSTRUCTIONS,
            },
        )

    if method == "ping":
        return _rpc_result(request_id, {})

    if method == "tools/list":
        return _rpc_result(request_id, {"tools": TOOL_DEFS})

    if method == "tools/call":
        if not isinstance(params, dict):
            return _rpc_error(request_id, -32602, "Invalid params")
        name = params.get("name")
        if not isinstance(name, str):
            return _rpc_error(request_id, -32602, "Missing tool name")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            return _rpc_error(request_id, -32602, "arguments must be an object")
        result = await dispatch_tool(name, arguments)
        return _rpc_result(request_id, result)

    if method == "resources/list":
        return _rpc_result(request_id, {"resources": []})

    if method == "prompts/list":
        return _rpc_result(request_id, {"prompts": []})

    if isinstance(method, str) and method.startswith("notifications/"):
        return None

    if request_id is None:
        return None

    return _rpc_error(request_id, -32601, f"Method not found: {method}")


def new_request_id() -> str:
    return str(uuid4())
