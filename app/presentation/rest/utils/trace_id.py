import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.infrastructure.utils.context import set_trace_id


class TraceIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware for generating and propagating a Trace ID for each request.
    """

    TRACE_HEADER = "X-Trace-ID"

    async def dispatch(self, request: Request, call_next) -> Response:
        # Use existing trace id if provided by client or gateway
        trace_id = request.headers.get(self.TRACE_HEADER)

        if not trace_id:
            trace_id = str(uuid.uuid4())

        # Attach trace id to request state
        request.state.trace_id = trace_id

        # set for global logging
        set_trace_id(trace_id)

        # Continue request processing
        response: Response = await call_next(request)

        # Add trace id to response headers
        response.headers[self.TRACE_HEADER] = trace_id

        return response
