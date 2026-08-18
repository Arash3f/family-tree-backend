import logging
from typing import Any

from graphql import GraphQLError
from strawberry.extensions import SchemaExtension

from app.core.config import settings
from app.presentation.rest.errors.error_resolver import resolve_message
from app.presentation.rest.utils.language import detect_language
from app.utils.app_exception import AppException

logger = logging.getLogger(__name__)

_UNEXPECTED_ERROR_MESSAGE = {
    "en": "An unexpected error occurred.",
    "fa": "خطای غیرمنتظره‌ای رخ داد.",
}


def app_exception_to_graphql_error(
    exc: AppException,
    *,
    lang: str = "en",
    trace_id: str | None = None,
) -> GraphQLError:
    message = resolve_message(exc.code, lang)
    extensions: dict[str, Any] = {
        "error_code": int(exc.code) if not isinstance(exc.code, str) else exc.code,
        "status": exc.status_code,
        "trace_id": trace_id,
    }
    if settings.is_development_like:
        extensions["detail"] = exc.detail
    return GraphQLError(
        message=message,
        extensions=extensions,
    )


def unexpected_error_to_graphql_error(
    exc: Exception,
    *,
    lang: str = "en",
    trace_id: str | None = None,
) -> GraphQLError:
    logger.exception("Unhandled exception in GraphQL resolver: %s", exc)
    message = _UNEXPECTED_ERROR_MESSAGE.get(lang, _UNEXPECTED_ERROR_MESSAGE["en"])
    extensions = {
        "error_code": "INTERNAL_SERVER_ERROR",
        "status": 500,
        "trace_id": trace_id,
    }
    if settings.is_development_like:
        extensions["detail"] = [str(exc)]
    return GraphQLError(
        message=message,
        extensions=extensions,
    )


class AppExceptionExtension(SchemaExtension):
    """Map domain AppException to GraphQL errors (aligned with REST error payload)."""

    async def resolve(self, _next, root, info, *args, **kwargs):
        try:
            result = _next(root, info, *args, **kwargs)
            if hasattr(result, "__await__"):
                result = await result
            return result
        except GraphQLError:
            raise
        except AppException as exc:
            request = info.context.request
            lang = detect_language(request)
            trace_id = getattr(request.state, "trace_id", None)
            raise app_exception_to_graphql_error(
                exc, lang=lang, trace_id=trace_id
            ) from exc
        except Exception as exc:
            request = info.context.request
            lang = detect_language(request)
            trace_id = getattr(request.state, "trace_id", None)
            raise unexpected_error_to_graphql_error(
                exc, lang=lang, trace_id=trace_id
            ) from exc
