import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import jwt

from app.application.interfaces.token_service import TokenService
from app.core.config import settings


class JWTService(TokenService):
    # Issue access tokens a few seconds early to absorb minor clock skew
    def create_access_token(self, user_id: UUID, session_id: UUID) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "sid": str(session_id),
            "type": "access",
            "iat": now - timedelta(seconds=5),
            "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }

        return jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    def create_refresh_token(self, user_id: UUID, session_id: UUID) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "sid": str(session_id),
            "jti": str(session_id),
            "type": "refresh",
            "iat": now - timedelta(seconds=5),
            "exp": now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        }

        return jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    def create_impersonation_token(
        self, target_user_id: UUID, actor_admin_id: UUID
    ) -> str:
        """Short-lived access token that signs the caller in as another user.

        Carries no `sid`: impersonation deliberately opens no login session, so
        nothing is stored server-side and the token simply dies at `exp`. The
        `imp` flag is what lets `get_current_user` skip the session lookup, and
        `act` records which admin is acting, for the audit trail.

        @param target_user_id - The user being impersonated.
        @param actor_admin_id - The admin performing the impersonation.

        @returns A signed JWT access token with no matching session row.
        """
        now = datetime.now(UTC)
        payload = {
            "sub": str(target_user_id),
            "type": "access",
            "imp": True,
            "act": str(actor_admin_id),
            "iat": now - timedelta(seconds=5),
            "exp": now + timedelta(minutes=settings.IMPERSONATION_TOKEN_EXPIRE_MINUTES),
        }

        return jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    def decode_token(self, token: str) -> dict:
        # python-jose has no leeway kwarg; tolerate small skew via early issuance
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require_exp": True, "require_sub": True},
        )

    def hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
