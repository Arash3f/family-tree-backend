from jose import jwt
from datetime import datetime, timedelta, timezone

from app.application.interfaces.token_service import TokenService
from app.core.config import setting


class JWTService(TokenService):
    def create_access_token(self, user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=setting.ACCESS_TOKEN_EXPIRE_MINUTES),
        }

        return jwt.encode(payload, setting.JWT_SECRET, algorithm=setting.JWT_ALGORITHM)

    def create_refresh_token(self, user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": datetime.now(timezone.utc)
            + timedelta(days=setting.REFRESH_TOKEN_EXPIRE_DAYS),
        }

        return jwt.encode(payload, setting.JWT_SECRET, algorithm=setting.JWT_ALGORITHM)

    def decode_token(self, token: str) -> dict:
        return jwt.decode(token, setting.JWT_SECRET, algorithms=[setting.JWT_ALGORITHM])
