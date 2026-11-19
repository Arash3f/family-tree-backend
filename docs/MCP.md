# MCP (Model Context Protocol)

Medium-weight AI surface for Family Tree: personal access tokens + a JSON-RPC
`POST /mcp` endpoint. No OAuth server — keep it simpler than Satba, still safe
enough for production with the flag off by default.

## Enable

```env
MCP_ENABLED=true
MCP_PUBLIC_URL=https://family.arash-alfooneh.ir/backend/mcp
MCP_TOKEN_DEFAULT_DAYS=90
MCP_TOKEN_MAX_ACTIVE=5
```

Apply migration `0026_mcp_tokens`.

## Panel

Signed-in users manage tokens under **Profile → AI connection (MCP)**:
create / list / revoke, plus a Cursor-style JSON snippet.

## Agent auth

`Authorization: Bearer ftmcp_…` (secret shown once at creation).

## Tools (read-only)

| Tool | Purpose |
|------|---------|
| `whoami` | Caller identity |
| `list_trees` | Trees the user can access |
| `search_persons` | Name search in a tree |
| `get_person` | One person |
| `get_person_card` | Parents / spouses / children |
| `get_relationship` | Closest kinship path |

Tree-scoped tools enforce the same membership `view` check as the REST API.
