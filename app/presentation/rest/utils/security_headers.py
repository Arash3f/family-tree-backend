from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach baseline security headers the app should own regardless of
    whatever reverse proxy sits in front of it in a given deployment."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
        )

        return response
