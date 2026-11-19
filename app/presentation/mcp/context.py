from contextvars import ContextVar

from app.domain.entities.user import User

#: The user authenticated for the current MCP request (set by auth middleware).
mcp_caller: ContextVar[User | None] = ContextVar("mcp_caller", default=None)


def get_mcp_caller() -> User:
    """Return the MCP caller or raise if the middleware did not set one."""
    user = mcp_caller.get()
    if user is None:
        from app.domain.exceptions.mcp_exceptions import McpInvalidTokenException

        raise McpInvalidTokenException(detail=["MCP caller missing"])
    return user
