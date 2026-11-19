import pytest

from app.presentation.mcp.protocol import handle_jsonrpc, list_tool_names


@pytest.mark.asyncio
async def test_initialize_returns_server_capabilities():
    response = await handle_jsonrpc(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-03-26", "capabilities": {}},
        }
    )
    assert response is not None
    assert response["id"] == 1
    assert response["result"]["protocolVersion"] == "2025-03-26"
    assert "tools" in response["result"]["capabilities"]


@pytest.mark.asyncio
async def test_tools_list_matches_catalog():
    response = await handle_jsonrpc(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    )
    assert response is not None
    names = [tool["name"] for tool in response["result"]["tools"]]
    assert names == list_tool_names()
    assert "whoami" in names
    assert "get_relationship" in names


@pytest.mark.asyncio
async def test_notification_returns_none():
    response = await handle_jsonrpc(
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
    )
    assert response is None


@pytest.mark.asyncio
async def test_unknown_method_errors():
    response = await handle_jsonrpc(
        {"jsonrpc": "2.0", "id": 9, "method": "nope/unknown", "params": {}}
    )
    assert response is not None
    assert response["error"]["code"] == -32601
