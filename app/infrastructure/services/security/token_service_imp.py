from datetime import datetime, timedelta, timezone

from jose import jwt

from app.application.interfaces.token_service import TokenService
from app.core.config import settings


class JWTService(TokenService):
    def create_access_token(self, user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }

        return jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    def create_refresh_token(self, user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        }

        return jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    def decode_token(self, token: str) -> dict:
        return jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
