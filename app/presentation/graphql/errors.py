from graphql import GraphQLError
from strawberry.extensions import SchemaExtension

from app.presentation.rest.errors.error_resolver import resolve_message
from app.presentation.rest.utils.language import detect_language
from app.utils.app_exception import AppException


def app_exception_to_graphql_error(
    exc: AppException,
    *,
    lang: str = "en",
    trace_id: str | None = None,
) -> GraphQLError:
    message = resolve_message(exc.code, lang)
    return GraphQLError(
        message=message,
        extensions={
            "error_code": int(exc.code) if not isinstance(exc.code, str) else exc.code,
            "status": exc.status_code,
            "detail": exc.detail,
            "trace_id": trace_id,
        },
    )


class AppExceptionExtension(SchemaExtension):
    """Map domain AppException to GraphQL errors (aligned with REST error payload)."""

    async def resolve(self, _next, root, info, *args, **kwargs):
        try:
            result = _next(root, info, *args, **kwargs)
            if hasattr(result, "__await__"):
                result = await result
            return result
        except AppException as exc:
            request = info.context.request
            lang = detect_language(request)
            trace_id = getattr(request.state, "trace_id", None)
            raise app_exception_to_graphql_error(
                exc, lang=lang, trace_id=trace_id
            ) from exc
