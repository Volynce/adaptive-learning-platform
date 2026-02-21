from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session


class NoActiveStageError(Exception):
    """У пользователя отсутствует активная стадия (status='active')."""


@dataclass(frozen=True)
class CurrentStage:
    user_id: int
    track_id: int
    track_name: str
    stage_id: int
    rank: str
    level: int
    status: str
    activated_at: datetime
    settings_version_id: int


def get_current_stage(db: Session, *, user_id: int) -> CurrentStage:
    """
    Read-only use-case: получить активную стадию пользователя.

    Источник истины: user_stage_progress (partial unique на active),
    поэтому ожидаем максимум одну запись.
    """
    row = db.execute(
        text(
            """
            SELECT
                usp.user_id,
                t.id   AS track_id,
                t.name AS track_name,
                usp.stage_id,
                s.rank,
                s.level,
                usp.status,
                usp.activated_at,
                usp.settings_version_id
            FROM user_stage_progress usp
            JOIN stages s ON s.id = usp.stage_id
            JOIN tracks t ON t.id = s.track_id
            WHERE usp.user_id = :uid
              AND usp.status = 'active'
            LIMIT 1
            """
        ),
        {"uid": user_id},
    ).fetchone()

    if row is None:
        raise NoActiveStageError()

    return CurrentStage(
        user_id=int(row[0]),
        track_id=int(row[1]),
        track_name=str(row[2]),
        stage_id=int(row[3]),
        rank=str(row[4]),
        level=int(row[5]),
        status=str(row[6]),
        activated_at=row[7],
        settings_version_id=int(row[8]),
    )