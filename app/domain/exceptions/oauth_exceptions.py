from fastapi import status

from app.utils.app_exception import AppException
from app.utils.error_codes import ErrorCode


class OAuthError(AppException):
    """OAuth protocol error (also mapped to RFC 6749 JSON by the OAuth filter)."""

    def __init__(
        self,
        *,
        oauth_error: str,
        description: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: list[str] | None = None,
    ):
        self.oauth_error = oauth_error
        self.oauth_error_description = description
        super().__init__(
            code=ErrorCode.OAUTH_ERROR,
            status_code=status_code,
            detail=detail or [description],
        )


class OAuthConsentNotFoundException(AppException):
    def __init__(self, detail: list[str] | None = None):
        super().__init__(
            code=ErrorCode.OAUTH_CONSENT_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or ["OAuth consent request not found"],
        )
