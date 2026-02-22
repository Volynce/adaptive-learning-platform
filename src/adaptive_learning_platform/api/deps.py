from __future__ import annotations

from typing import Generator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from adaptive_learning_platform.config.settings import Settings, get_settings
from adaptive_learning_platform.infrastructure.db.session import get_session
from adaptive_learning_platform.infrastructure.security.jwt import JWTDecodeError, decode_token

_bearer = HTTPBearer(auto_error=False)


def settings_dep() -> Settings:
    """
    Dependency для FastAPI.

    Сейчас:
    - отдаём типизированные настройки из единого источника (pydantic-settings).

    Позже:
    - можно расширять правила авторизации (roles/permissions), не меняя бизнес-код use-case.
    """
    return get_settings()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency для выдачи SQLAlchemy Session.

    Важно:
    - это generator-функция (yield), иначе FastAPI передаст generator-объект,
      и попытка вызвать db.execute(...) завершится ошибкой.
    """
    yield from get_session()


def current_user_id(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> int:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Отсутствует Authorization: Bearer токен")

    try:
        payload = decode_token(creds.credentials)
    except JWTDecodeError:
        raise HTTPException(status_code=401, detail="Некорректный токен")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Некорректный тип токена")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Некорректный токен (нет sub)")

    try:
        return int(sub)
    except ValueError:
        raise HTTPException(status_code=401, detail="Некорректный токен (sub не int)")


def current_admin_id(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> int:
    """
    Dependency: извлекает admin_id из JWT.

    Правила:
    - token type должен быть access
    - scope должен быть 'admin'
    - sub должен быть int
    """
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Отсутствует Authorization: Bearer токен")

    try:
        payload = decode_token(creds.credentials)
    except JWTDecodeError:
        raise HTTPException(status_code=401, detail="Некорректный токен")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Некорректный токен")

    if payload.get("scope") != "admin":
        raise HTTPException(status_code=401, detail="Некорректный токен")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Некорректный токен")

    try:
        return int(sub)
    except ValueError:
        raise HTTPException(status_code=401, detail="Некорректный токен")


def current_user(
    db: Session = Depends(get_db),
    user_id: int = Depends(current_user_id),
) -> dict:
    row = db.execute(
        text("SELECT id, email, full_name, track_id FROM users WHERE id = :id"),
        {"id": user_id},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return {"id": int(row[0]), "email": row[1], "full_name": row[2], "track_id": int(row[3])}