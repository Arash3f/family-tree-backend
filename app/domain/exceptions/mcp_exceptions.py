from app.utils.app_exception import AppException
from app.utils.error_codes import ErrorCode


class McpDisabledException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.MCP_DISABLED,
            status_code=404,
            detail=detail or ["MCP is disabled on this server"],
        )


class McpTokenNotFoundException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.MCP_TOKEN_NOT_FOUND,
            status_code=404,
            detail=detail or ["MCP token not found"],
        )


class McpTokenLimitException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.MCP_TOKEN_LIMIT,
            status_code=400,
            detail=detail or ["Too many active MCP tokens"],
        )


class McpInvalidTokenException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.MCP_INVALID_TOKEN,
            status_code=401,
            detail=detail or ["Invalid or expired MCP token"],
        )
