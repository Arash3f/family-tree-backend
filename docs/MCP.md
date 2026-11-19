# MCP for ChatGPT (Family Tree)

Remote MCP so ChatGPT (and other agents) can read the caller's family trees.

## What you get

- `POST /mcp` — JSON-RPC tools (Streamable-HTTP compatible JSON responses)
- OAuth 2.1 authorization code + PKCE (`S256`)
- Protected-resource + authorization-server discovery
- DCR (`POST /oauth/register`) and CIMD (`https://…` client_id, chatgpt.com allowlist)
- Personal `ftmcp_…` tokens still work for Cursor-style clients

## Enable

```env
MCP_ENABLED=true
MCP_PUBLIC_URL=https://family.arash-alfooneh.ir/backend/mcp
MCP_RESOURCE_URL=https://family.arash-alfooneh.ir/backend/mcp
OAUTH_ISSUER=https://family.arash-alfooneh.ir/backend
OAUTH_CONSENT_URL=https://family.arash-alfooneh.ir/fa/oauth/consent
```

Apply migrations `0026_mcp_tokens` and `0027_oauth_mcp`.

## ChatGPT setup

1. Deploy with the env above (public HTTPS).
2. In ChatGPT: add a custom MCP server / plugin with Server URL = `MCP_PUBLIC_URL`.
3. Choose OAuth. ChatGPT will:
   - read `/.well-known/oauth-protected-resource`
   - register or use CIMD
   - open `/oauth/authorize` → your consent page → token exchange
4. User signs in on Family Tree, approves, returns to ChatGPT.

Discovery URLs (under the issuer / API base):

| Path | Role |
|------|------|
| `/.well-known/oauth-protected-resource` | Resource metadata |
| `/.well-known/oauth-authorization-server` | AS metadata |
| `/oauth/authorize` | Start login+consent |
| `/oauth/token` | Code / refresh exchange |
| `/oauth/register` | Dynamic client registration |

Scope: `family-tree:read`.

## Tools

| Tool | Purpose |
|------|---------|
| `whoami` | Caller identity |
| `list_trees` | Trees the user can access |
| `search_persons` | Name search in a tree |
| `get_person` | One person |
| `get_person_card` | Parents / spouses / children |
| `get_relationship` | Closest kinship path |

## Panel

**Profile → AI connection (MCP)** still mints personal tokens for non-OAuth clients and shows the ChatGPT server URL.
