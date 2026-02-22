from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from adaptive_learning_platform.config.settings import get_settings


class JWTDecodeError(Exception):
    """Токен не удалось декодировать/проверить."""


def create_access_token(*, subject: str, scope: str = "user", extra: dict[str, Any] | None = None) -> str:
    """
    Выпуск access JWT.

    Инварианты проекта:
    - type = "access"
    - sub = идентификатор субъекта (user_id или admin_id) в виде строки
    - scope = "user" | "admin" (для разделения областей доступа)
    - iat/exp задаются в UTC
    """
    s = get_settings()
    now = datetime.now(timezone.utc)

    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "scope": scope,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=s.JWT_ACCESS_TTL_MINUTES)).timestamp()),
    }

    # Дополнительные claim-ы (если нужны), но не даём перезаписать ключевые поля.
    if extra:
        for k, v in extra.items():
            if k in payload:
                continue
            payload[k] = v

    return jwt.encode(payload, s.JWT_SECRET, algorithm=s.JWT_ALG)


def decode_token(token: str) -> dict[str, Any]:
    """
    Декодирование и проверка подписи JWT.
    """
    s = get_settings()
    try:
        payload = jwt.decode(token, s.JWT_SECRET, algorithms=[s.JWT_ALG])
        # jose возвращает dict, типизируем явно
        return dict(payload)
    except JWTError as e:
        raise JWTDecodeError("Некорректный токен") from e