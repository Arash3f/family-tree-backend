from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.application.use_cases.mcp.mcp_token_use_cases import (
    MCP_TOKEN_PREFIX,
    mint_mcp_token_secret,
)
from app.domain.entities.mcp_token import McpToken


def test_mint_mcp_token_secret_has_prefix_and_entropy():
    first = mint_mcp_token_secret()
    second = mint_mcp_token_secret()
    assert first.startswith(MCP_TOKEN_PREFIX)
    assert second.startswith(MCP_TOKEN_PREFIX)
    assert first != second
    assert len(first) > len(MCP_TOKEN_PREFIX) + 20


def test_mcp_token_is_active_respects_expiry_and_revoke():
    token = McpToken(
        user_id=uuid4(),
        name="test",
        token_hash="a" * 64,
        token_prefix="ftmcp_xxxxxx",
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    assert token.is_active()

    token.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    assert not token.is_active()

    token.expires_at = None
    assert token.is_active()
    token.revoke()
    assert not token.is_active()
