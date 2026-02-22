from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session


class EligibilityError(Exception):
    pass


@dataclass(frozen=True)
class MissingArticle:
    article_id: int
    module_id: int
    module_name: str
    title: str
    kind: str  # required/optional


@dataclass(frozen=True)
class EligibilityReport:
    user_id: int
    stage_id: int
    rank: str
    level: int
    settings_version_id: int
    required_total: int
    required_done: int
    optional_total: int
    optional_done: int
    missing_required: List[MissingArticle]
    missing_optional: List[MissingArticle]
    eligible: bool


def get_level_exam_eligibility(db: Session, *, user_id: int) -> EligibilityReport:
    # 1) активная стадия
    row = db.execute(
        text(
            """
            SELECT usp.stage_id, usp.settings_version_id, s.rank, s.level
            FROM user_stage_progress usp
            JOIN stages s ON s.id = usp.stage_id
            WHERE usp.user_id=:uid AND usp.status='active'
            LIMIT 1
            """
        ),
        {"uid": user_id},
    ).fetchone()
    if row is None:
        raise EligibilityError("У пользователя нет активной стадии")

    stage_id = int(row[0])
    settings_version_id = int(row[1])
    rank = str(row[2])
    level = int(row[3])

    # 2) агрегаты по required/optional
    cnt = db.execute(
        text(
            """
            SELECT
              COUNT(*) FILTER (WHERE kind='required')::int AS required_total,
              COUNT(*) FILTER (WHERE kind='required' AND minitest_passed=true)::int AS required_done,
              COUNT(*) FILTER (WHERE kind='optional')::int AS optional_total,
              COUNT(*) FILTER (WHERE kind='optional' AND is_read=true)::int AS optional_done
            FROM user_stage_articles
            WHERE user_id=:uid AND stage_id=:sid
            """
        ),
        {"uid": user_id, "sid": stage_id},
    ).fetchone()

    required_total = int(cnt[0] or 0)
    required_done = int(cnt[1] or 0)
    optional_total = int(cnt[2] or 0)
    optional_done = int(cnt[3] or 0)

    # 3) списки незакрытых
    miss_req_rows = db.execute(
        text(
            """
            SELECT a.id, m.id, m.name, a.title
            FROM user_stage_articles usa
            JOIN articles a ON a.id=usa.article_id
            JOIN modules m ON m.id=a.module_id
            WHERE usa.user_id=:uid AND usa.stage_id=:sid
              AND usa.kind='required'
              AND usa.minitest_passed=false
            ORDER BY m.id, a.id
            """
        ),
        {"uid": user_id, "sid": stage_id},
    ).fetchall()

    miss_opt_rows = db.execute(
        text(
            """
            SELECT a.id, m.id, m.name, a.title
            FROM user_stage_articles usa
            JOIN articles a ON a.id=usa.article_id
            JOIN modules m ON m.id=a.module_id
            WHERE usa.user_id=:uid AND usa.stage_id=:sid
              AND usa.kind='optional'
              AND usa.is_read=false
            ORDER BY m.id, a.id
            """
        ),
        {"uid": user_id, "sid": stage_id},
    ).fetchall()

    missing_required = [
        MissingArticle(article_id=int(r[0]), module_id=int(r[1]), module_name=str(r[2]), title=str(r[3]), kind="required")
        for r in miss_req_rows
    ]
    missing_optional = [
        MissingArticle(article_id=int(r[0]), module_id=int(r[1]), module_name=str(r[2]), title=str(r[3]), kind="optional")
        for r in miss_opt_rows
    ]

    eligible = (required_total == required_done) and (optional_total == optional_done) and required_total > 0

    return EligibilityReport(
        user_id=user_id,
        stage_id=stage_id,
        rank=rank,
        level=level,
        settings_version_id=settings_version_id,
        required_total=required_total,
        required_done=required_done,
        optional_total=optional_total,
        optional_done=optional_done,
        missing_required=missing_required,
        missing_optional=missing_optional,
        eligible=eligible,
    )