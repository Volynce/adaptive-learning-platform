from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from adaptive_learning_platform.api.deps import get_db
from adaptive_learning_platform.infrastructure.security.jwt import JWTDecodeError, decode_token

router = APIRouter()

_bearer = HTTPBearer(auto_error=False)


def current_user_id(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> int:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Отсутствует Authorization: Bearer токен")

    try:
        payload = decode_token(creds.credentials)
    except JWTDecodeError:
        raise HTTPException(status_code=401, detail="Некорректный токен")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Некорректный токен (нет sub)")

    try:
        return int(sub)
    except ValueError:
        raise HTTPException(status_code=401, detail="Некорректный токен (sub не int)")


@router.get("/me", summary="Текущий пользователь (protected)")
def me(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    row = db.execute(
        text("SELECT id, email, full_name, track_id FROM users WHERE id = :id"),
        {"id": user_id},
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return {"id": int(row[0]), "email": row[1], "full_name": row[2], "track_id": int(row[3])}