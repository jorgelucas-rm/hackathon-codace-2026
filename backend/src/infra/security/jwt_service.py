from datetime import datetime, timedelta, timezone

import jwt

from src.app.model.enum import ErrorCode
from src.environments import JWT_ALGORITHM, JWT_SECRET, JWT_TOKEN_EXPIRE
from src.infra.exception.exceptions import UnauthorizedException


class JWTService:

    @staticmethod
    def create_access_token(sub: int, level: int, auth_type: int) -> str:
        payload = {
            "sub": str(sub),
            "role": level,
            "auth_type": auth_type,
            "iat": datetime.now(tz=timezone.utc),
            "exp": datetime.now(tz=timezone.utc)
            + timedelta(minutes=int(JWT_TOKEN_EXPIRE)),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException(
                message="Expired token",
                error_code=ErrorCode.EXPIRED_TOKEN,
            )
        except jwt.InvalidTokenError:
            raise UnauthorizedException(
                message="Invalid token",
                error_code=ErrorCode.INVALID_TOKEN,
            )
