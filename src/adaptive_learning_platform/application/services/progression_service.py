from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class ProgressAction:
    """
    Минимальный контракт прогрессии для API.

    action:
      - "none"            : ничего не меняем
      - "auto_advanced"   : следующая стадия активирована автоматически
      - "pending_approval": требуется подтверждение админом (межранговый переход / выпуск)
    """
    action: str
    from_stage_id: int
    to_stage_id: int | None


class StageNotFound(Exception):
    pass


class NextStageNotFound(Exception):
    pass


def _get_stage_meta(db: Session, *, stage_id: int) -> tuple[int, str, int]:
    row = db.execute(
        text("SELECT track_id, rank, level FROM stages WHERE id=:sid"),
        {"sid": stage_id},
    ).fetchone()
    if row is None:
        raise StageNotFound(f"Стадия не найдена: stage_id={stage_id}")
    return int(row[0]), str(row[1]), int(row[2])


def _find_stage_id(db: Session, *, track_id: int, rank: str, level: int) -> int:
    row = db.execute(
        text(
            """
            SELECT id
            FROM stages
            WHERE track_id=:tid AND rank=:rank AND level=:lvl
            """
        ),
        {"tid": track_id, "rank": rank, "lvl": level},
    ).fetchone()
    if row is None:
        raise NextStageNotFound(f"Следующая стадия не найдена: track_id={track_id} rank={rank} level={level}")
    return int(row[0])


def apply_progress_after_level_exam_pass(
    db: Session,
    *,
    user_id: int,
    stage_id: int,
    settings_version_id: int,
) -> ProgressAction:
    """
    Применяет доменную прогрессию сразу после PASS level-exam.

    ВАЖНО (архитектурное правило):
    - функция НЕ делает commit/rollback,
    - вызывается внутри submit_level_exam() и должна работать транзакционно.
    """
    track_id, rank, level = _get_stage_meta(db, stage_id=stage_id)

    # 1) Trainee_0 -> Junior_1 (только через approval)
    if rank == "trainee" and level == 0:
        to_stage_id = _find_stage_id(db, track_id=track_id, rank="junior", level=1)

        # закрываем текущую стадию в статус pending_approval
        db.execute(
            text(
                """
                UPDATE user_stage_progress
                SET status='pending_approval', completed_at=now()
                WHERE user_id=:uid AND stage_id=:sid AND status='active'
                """
            ),
            {"uid": user_id, "sid": stage_id},
        )

        # создаём заявку на подтверждение перехода
        db.execute(
            text(
                """
                INSERT INTO approval_requests(user_id, from_stage_id, to_stage_id, type, status, created_at, comment)
                VALUES (:uid, :from_sid, :to_sid, 'rank_transition', 'pending', now(),
                        'Авто: Trainee_0 level-exam PASS, требуется подтверждение перехода')
                """
            ),
            {"uid": user_id, "from_sid": stage_id, "to_sid": to_stage_id},
        )

        return ProgressAction(action="pending_approval", from_stage_id=stage_id, to_stage_id=to_stage_id)

    # 2) Внутри ранга: level 1 -> 2 -> 3 (автоматически)
    if rank in ("junior", "middle", "senior") and level in (1, 2):
        to_stage_id = _find_stage_id(db, track_id=track_id, rank=rank, level=level + 1)

        # сначала завершаем текущую active стадию
        db.execute(
            text(
                """
                UPDATE user_stage_progress
                SET status='completed', completed_at=now()
                WHERE user_id=:uid AND stage_id=:sid AND status='active'
                """
            ),
            {"uid": user_id, "sid": stage_id},
        )

        # затем активируем следующую (с той же settings_version_id)
        db.execute(
            text(
                """
                INSERT INTO user_stage_progress(user_id, stage_id, settings_version_id, status, activated_at)
                VALUES (:uid, :to_sid, :sv, 'active', now())
                """
            ),
            {"uid": user_id, "to_sid": to_stage_id, "sv": settings_version_id},
        )

        return ProgressAction(action="auto_advanced", from_stage_id=stage_id, to_stage_id=to_stage_id)

    # 3) Конец ранга (level=3): межранговый переход через approval / выпуск через graduation approval
    if rank in ("junior", "middle", "senior") and level == 3:
        if rank == "junior":
            to_stage_id = _find_stage_id(db, track_id=track_id, rank="middle", level=1)
            req_type = "rank_transition"
            comment = "Авто: Junior_3 level-exam PASS, требуется подтверждение перехода в Middle_1"
        elif rank == "middle":
            to_stage_id = _find_stage_id(db, track_id=track_id, rank="senior", level=1)
            req_type = "rank_transition"
            comment = "Авто: Middle_3 level-exam PASS, требуется подтверждение перехода в Senior_1"
        else:
            # senior level=3 -> выпуск (graduation)
            to_stage_id = None
            req_type = "graduation"
            comment = "Авто: Senior_3 PASS, требуется подтверждение выпуска (graduation)"

        db.execute(
            text(
                """
                UPDATE user_stage_progress
                SET status='pending_approval', completed_at=now()
                WHERE user_id=:uid AND stage_id=:sid AND status='active'
                """
            ),
            {"uid": user_id, "sid": stage_id},
        )

        db.execute(
            text(
                """
                INSERT INTO approval_requests(user_id, from_stage_id, to_stage_id, type, status, created_at, comment)
                VALUES (:uid, :from_sid, :to_sid, :type, 'pending', now(), :comment)
                """
            ),
            {"uid": user_id, "from_sid": stage_id, "to_sid": to_stage_id, "type": req_type, "comment": comment},
        )

        return ProgressAction(action="pending_approval", from_stage_id=stage_id, to_stage_id=to_stage_id)

    # 4) По умолчанию — ничего не делаем
    return ProgressAction(action="none", from_stage_id=stage_id, to_stage_id=None)
