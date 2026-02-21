from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from adaptive_learning_platform.api.deps import get_db
from adaptive_learning_platform.infrastructure.db.session import ping_db

router = APIRouter()


@router.get("/db", summary="Проверка связи API ↔ БД")
def health_db(db: Session = Depends(get_db)) -> dict:
    ping_db(db)
    return {"status": "ok", "db": "ok"}