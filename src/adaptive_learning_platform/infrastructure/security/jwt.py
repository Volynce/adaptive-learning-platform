from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt

from adaptive_learning_platform.config.settings import get_settings


class JWTDecodeError(Exception):
    pass


def create_access_token(*, subject: str, extra: Dict[str, Any] | None = None) -> str:
    """
    Создаёт access JWT.
    subject: строковый идентификатор пользователя (обычно user_id).
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)

    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.JWT_ACCESS_TTL_MINUTES)).timestamp()),
        "type": "access",
    }
    if extra:
        payload.update(extra)

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except JWTError as e:
        raise JWTDecodeError(str(e)) from e