"""Shared OAuth / MCP authorization constants for ChatGPT connectors."""

MCP_SCOPE = "family-tree:read"
MCP_ACCESS_TOKEN_TYPE = "mcp_access"
CONSENT_TTL_MINUTES = 15
AUTH_CODE_TTL_MINUTES = 10
MCP_ACCESS_TTL_MINUTES = 15
MCP_REFRESH_TTL_DAYS = 30

# Hosts allowed when resolving a CIMD `client_id` URL (SSRF allowlist).
CIMD_ALLOWED_HOST_SUFFIXES = (
    "chatgpt.com",
    "openai.com",
)
