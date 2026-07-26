import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import jwt

from app.application.interfaces.token_service import TokenService
from app.core.config import settings


class JWTService(TokenService):
    # Issue access tokens a few seconds early to absorb minor clock skew
    def create_access_token(self, user_id: UUID, session_id: UUID) -> str:
        now = datetime.now(timezone.utc)
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
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "sid": str(session_id),
            "jti": str(session_id),
            "type": "refresh",
            "iat": now - timedelta(seconds=5),
            "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
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
