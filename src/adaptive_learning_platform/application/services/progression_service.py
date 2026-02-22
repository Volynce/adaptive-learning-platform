from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


class ProgressionError(Exception):
    pass


@dataclass(frozen=True)
class ProgressAction:
    """
    Результат доменного шага прогрессии после PASS.
    action:
      - advanced: автоматический переход внутри ранга (level 1->2, 2->3)
      - pending_approval: стадия завершена, требуется подтверждение админа для перехода на следующий rank
      - none: прогрессия не выполняется (например, level=3 — дальше будет rank-final)
    """
    action: str
    from_stage_id: int
    to_stage_id: Optional[int] = None


_RANK_ORDER = ["trainee", "junior", "middle", "senior"]


def apply_progress_after_level_exam_pass(
    db: Session, *, user_id: int, stage_id: int, settings_version_id: int
) -> ProgressAction:
    # 1) Получаем параметры стадии (rank/level/track_id)
    srow = db.execute(
        text("SELECT track_id, rank, level FROM stages WHERE id=:sid"),
        {"sid": stage_id},
    ).fetchone()
    if srow is None:
        raise ProgressionError("Стадия не найдена")

    track_id = int(srow[0])
    rank = str(srow[1])
    level = int(srow[2])

    # 2) Вариант A: внутри ранга (junior/middle/senior) level 1->2->3 делаем auto-advance
    if rank in ("junior", "middle", "senior") and level in (1, 2):
        next_stage = db.execute(
            text(
                """
                SELECT id
                FROM stages
                WHERE track_id=:tid AND rank=:rank AND level=:lvl
                LIMIT 1
                """
            ),
            {"tid": track_id, "rank": rank, "lvl": level + 1},
        ).fetchone()
        if next_stage is None:
            raise ProgressionError(f"Не найдена следующая стадия {rank}_{level+1} в track_id={track_id}")
        next_stage_id = int(next_stage[0])

        # Завершаем текущую активную стадию
        updated = db.execute(
            text(
                """
                UPDATE user_stage_progress
                SET status='completed', completed_at=now()
                WHERE user_id=:uid AND stage_id=:sid AND status='active'
                """
            ),
            {"uid": user_id, "sid": stage_id},
        )
        if updated.rowcount != 1:
            raise ProgressionError("Не удалось завершить текущую стадию (ожидалась status='active')")

        # Активируем следующую (создаём запись, либо активируем существующую)
        db.execute(
            text(
                """
                INSERT INTO user_stage_progress(user_id, stage_id, settings_version_id, status, activated_at, completed_at)
                VALUES (:uid, :nsid, :sv, 'active', now(), NULL)
                ON CONFLICT (user_id, stage_id)
                DO UPDATE SET
                  status='active',
                  settings_version_id=EXCLUDED.settings_version_id,
                  activated_at=COALESCE(user_stage_progress.activated_at, now()),
                  completed_at=NULL
                """
            ),
            {"uid": user_id, "nsid": next_stage_id, "sv": settings_version_id},
        )

        return ProgressAction(action="advanced", from_stage_id=stage_id, to_stage_id=next_stage_id)

    # 3) Вариант B: Trainee_0 после PASS — требуется подтверждение перехода на Junior_1
    if rank == "trainee" and level == 0:
        # определяем следующую стадию junior_1
        next_stage = db.execute(
            text(
                """
                SELECT id
                FROM stages
                WHERE track_id=:tid AND rank='junior' AND level=1
                LIMIT 1
                """
            ),
            {"tid": track_id},
        ).fetchone()
        next_stage_id = int(next_stage[0]) if next_stage else None

        updated = db.execute(
            text(
                """
                UPDATE user_stage_progress
                SET status='pending_approval', completed_at=now()
                WHERE user_id=:uid AND stage_id=:sid AND status='active'
                """
            ),
            {"uid": user_id, "sid": stage_id},
        )
        if updated.rowcount != 1:
            raise ProgressionError("Не удалось перевести стадию в pending_approval (ожидалась status='active')")

        # создаём approval_request (idempotent для pending)
        db.execute(
            text(
                """
                INSERT INTO approval_requests(user_id, from_stage_id, to_stage_id, type, status, created_at, comment)
                VALUES (:uid, :fsid, :tsid, 'rank_transition', 'pending', now(),
                        'Авто: Trainee_0 level-exam PASS, требуется подтверждение перехода')
                ON CONFLICT (user_id, from_stage_id) WHERE status='pending' DO NOTHING
                """
            ),
            {"uid": user_id, "fsid": stage_id, "tsid": next_stage_id},
        )

        return ProgressAction(action="pending_approval", from_stage_id=stage_id, to_stage_id=next_stage_id)

    # 4) Иначе: level=3 (или иные случаи) — прогрессию НЕ делаем (дальше будет rank-final)
    return ProgressAction(action="none", from_stage_id=stage_id, to_stage_id=None)