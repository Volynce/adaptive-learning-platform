from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session


class ContentError(Exception):
    pass


class MissingDiagnostika(ContentError):
    pass


class AlreadyAssigned(ContentError):
    pass


class MissingArticles(ContentError):
    pass


class NotTraineeStage(ContentError):
    """Оставлено для обратной совместимости, но больше не используется."""
    pass


class WrongArticleKind(ContentError):
    pass


@dataclass(frozen=True)
class AssignedArticle:
    article_id: int
    module_id: int
    module_name: str
    title: str
    content_ref: str
    kind: str  # required/optional
    is_read: bool
    minitest_passed: bool


def _get_active_stage_ctx(db: Session, user_id: int) -> dict:
    row = db.execute(
        text(
            """
            SELECT
              usp.stage_id,
              usp.settings_version_id,
              s.rank,
              s.level,
              t.id as track_id,
              t.name as track_name
            FROM user_stage_progress usp
            JOIN stages s ON s.id = usp.stage_id
            JOIN tracks t ON t.id = s.track_id
            WHERE usp.user_id = :uid AND usp.status='active'
            FOR UPDATE
            """
        ),
        {"uid": user_id},
    ).fetchone()

    if row is None:
        raise ContentError("У пользователя нет активной стадии")

    return {
        "stage_id": int(row[0]),
        "settings_version_id": int(row[1]),
        "rank": str(row[2]),
        "level": int(row[3]),
        "track_id": int(row[4]),
        "track_name": str(row[5]),
    }


def _is_optional_title(title: str) -> bool:
    # MVP-правило: kind кодируется в title (seed делает "... — optional/required")
    return "optional" in title.lower()


def _is_required_title(title: str) -> bool:
    return "required" in title.lower()


def assign_content_for_current_stage(db: Session, *, user_id: int) -> dict:
    """
    Назначение статей на текущую активную стадию.

    Правило (MVP):
    - optional: по content_optional_per_module на каждый модуль трека,
               выбираются статьи с признаком optional в title.
    - required: по 1 статье на каждый из K слабых модулей,
                выбираются статьи с признаком required в title.

    Слабость (пока baseline):
    - errors = total_cnt - correct_cnt из diagnostika_module_stats.
    """
    ctx = _get_active_stage_ctx(db, user_id)
    stage_id = ctx["stage_id"]
    settings_version_id = ctx["settings_version_id"]
    rank = ctx["rank"]
    level = ctx["level"]
    track_id = ctx["track_id"]

    # запрет повторного назначения (если уже есть хотя бы 1 статья на этой стадии)
    exists = db.execute(
        text(
            """
            SELECT 1
            FROM user_stage_articles
            WHERE user_id=:uid AND stage_id=:sid
            LIMIT 1
            """
        ),
        {"uid": user_id, "sid": stage_id},
    ).fetchone()
    if exists is not None:
        raise AlreadyAssigned("Контент уже назначен на текущую стадию")

    # настройки выдачи
    srow = db.execute(
        text(
            """
            SELECT content_k_weak_modules, content_optional_per_module
            FROM track_settings
            WHERE settings_version_id = :sv
            """
        ),
        {"sv": settings_version_id},
    ).fetchone()
    if srow is None:
        raise ContentError("Отсутствуют track_settings для активной версии настроек")

    k_weak = int(srow[0])
    optional_per_module = int(srow[1])

    # diagnostika_id (один раз на user)
    drow = db.execute(
        text("SELECT id FROM diagnostika_results WHERE user_id=:uid LIMIT 1"),
        {"uid": user_id},
    ).fetchone()
    if drow is None:
        raise MissingDiagnostika("Нет diagnostika_results. Сначала пройдите входную диагностику.")
    diagnostika_id = int(drow[0])

    # слабости по модулям: errors = total - correct
    weak_rows = db.execute(
        text(
            """
            SELECT module_id, (total_cnt - correct_cnt) AS errors
            FROM diagnostika_module_stats
            WHERE diagnostika_id = :did
            ORDER BY errors DESC, module_id ASC
            LIMIT :k
            """
        ),
        {"did": diagnostika_id, "k": k_weak},
    ).fetchall()
    weak_module_ids = [int(r[0]) for r in weak_rows]

    # все модули трека
    mrows = db.execute(
        text("SELECT id, name FROM modules WHERE track_id=:tid ORDER BY id"),
        {"tid": track_id},
    ).fetchall()
    modules = [{"id": int(r[0]), "name": str(r[1])} for r in mrows]

    selected_optional: Dict[int, List[dict]] = {}
    selected_required: Dict[int, List[dict]] = {}

    for m in modules:
        mid = m["id"]

        arows = db.execute(
            text(
                """
                SELECT id, title, content_ref
                FROM articles
                WHERE module_id=:mid
                  AND target_rank=:r
                  AND target_level=:l
                  AND is_active=true
                ORDER BY id
                """
            ),
            {"mid": mid, "r": rank, "l": level},
        ).fetchall()

        all_articles = [{"id": int(r[0]), "title": str(r[1]), "content_ref": str(r[2])} for r in arows]

        # Разделяем статьи по kind через title (MVP-правило)
        optional_candidates = [a for a in all_articles if _is_optional_title(a["title"])]
        required_candidates = [a for a in all_articles if _is_required_title(a["title"])]

        if len(optional_candidates) < optional_per_module:
            raise MissingArticles(
                f"Недостаточно optional-статей для module_id={mid} на rank={rank}, level={level}: "
                f"нужно {optional_per_module}, есть {len(optional_candidates)}"
            )

        opt = optional_candidates[:optional_per_module]
        selected_optional[mid] = opt

        if mid in weak_module_ids:
            # required: 1 статья (может совпадать с optional только если title криво размечен)
            remaining_required = [a for a in required_candidates if a["id"] not in {x["id"] for x in opt}]
            if len(remaining_required) < 1:
                raise MissingArticles(
                    f"Недостаточно required-статей для weak module_id={mid} на rank={rank}, level={level}: "
                    f"нужно >=1 (отдельно от optional)"
                )
            selected_required[mid] = [remaining_required[0]]

    # запись назначений
    assigned_optional = 0
    assigned_required = 0

    for m in modules:
        mid = m["id"]

        for a in selected_optional[mid]:
            db.execute(
                text(
                    """
                    INSERT INTO user_stage_articles(user_id, stage_id, article_id, kind, assigned_at)
                    VALUES (:uid, :sid, :aid, 'optional', now())
                    """
                ),
                {"uid": user_id, "sid": stage_id, "aid": a["id"]},
            )
            assigned_optional += 1

        if mid in selected_required:
            for a in selected_required[mid]:
                db.execute(
                    text(
                        """
                        INSERT INTO user_stage_articles(user_id, stage_id, article_id, kind, assigned_at)
                        VALUES (:uid, :sid, :aid, 'required', now())
                        """
                    ),
                    {"uid": user_id, "sid": stage_id, "aid": a["id"]},
                )
                assigned_required += 1

    return {
        "stage_id": stage_id,
        "diagnostika_id": diagnostika_id,
        "rank": rank,
        "level": level,
        "assigned_optional": assigned_optional,
        "assigned_required": assigned_required,
        "weak_module_ids": weak_module_ids,
    }


def list_my_stage_articles(db: Session, *, user_id: int) -> List[AssignedArticle]:
    ctx = db.execute(
        text(
            """
            SELECT usp.stage_id
            FROM user_stage_progress usp
            WHERE usp.user_id=:uid AND usp.status='active'
            LIMIT 1
            """
        ),
        {"uid": user_id},
    ).fetchone()
    if ctx is None:
        return []
    stage_id = int(ctx[0])

    rows = db.execute(
        text(
            """
            SELECT
              a.id as article_id,
              m.id as module_id,
              m.name as module_name,
              a.title,
              a.content_ref,
              usa.kind,
              usa.is_read,
              usa.minitest_passed
            FROM user_stage_articles usa
            JOIN articles a ON a.id = usa.article_id
            JOIN modules m ON m.id = a.module_id
            WHERE usa.user_id=:uid AND usa.stage_id=:sid
            ORDER BY usa.kind DESC, m.id, a.id
            """
        ),
        {"uid": user_id, "sid": stage_id},
    ).fetchall()

    return [
        AssignedArticle(
            article_id=int(r[0]),
            module_id=int(r[1]),
            module_name=str(r[2]),
            title=str(r[3]),
            content_ref=str(r[4]),
            kind=str(r[5]),
            is_read=bool(r[6]),
            minitest_passed=bool(r[7]),
        )
        for r in rows
    ]


def mark_optional_read(db: Session, *, user_id: int, article_id: int) -> None:
    # читаем текущую стадию
    srow = db.execute(
        text("SELECT stage_id FROM user_stage_progress WHERE user_id=:uid AND status='active' LIMIT 1"),
        {"uid": user_id},
    ).fetchone()
    if srow is None:
        raise ContentError("У пользователя нет активной стадии")
    stage_id = int(srow[0])

    # проверяем kind
    krow = db.execute(
        text(
            """
            SELECT kind, is_read
            FROM user_stage_articles
            WHERE user_id=:uid AND stage_id=:sid AND article_id=:aid
            """
        ),
        {"uid": user_id, "sid": stage_id, "aid": article_id},
    ).fetchone()
    if krow is None:
        raise ContentError("Статья не назначена пользователю на текущей стадии")

    kind = str(krow[0])
    if kind != "optional":
        raise WrongArticleKind("Отметка read допустима только для optional статей")

    db.execute(
        text(
            """
            UPDATE user_stage_articles
            SET is_read=true, read_at=now()
            WHERE user_id=:uid AND stage_id=:sid AND article_id=:aid AND is_read=false
            """
        ),
        {"uid": user_id, "sid": stage_id, "aid": article_id},
    )