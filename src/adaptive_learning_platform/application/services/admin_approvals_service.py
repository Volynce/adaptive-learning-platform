from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


class ApprovalError(Exception):
    pass


class ApprovalNotFound(ApprovalError):
    pass


class ApprovalAlreadyProcessed(ApprovalError):
    pass


class ApprovalInvalid(ApprovalError):
    pass


@dataclass(frozen=True)
class PendingApprovalRow:
    request_id: int
    user_id: int
    user_email: str
    from_stage_id: int
    to_stage_id: Optional[int]
    type: str
    created_at: str


def list_pending_approvals(db: Session) -> list[PendingApprovalRow]:
    rows = db.execute(
        text(
            """
            SELECT ar.id, ar.user_id, u.email, ar.from_stage_id, ar.to_stage_id, ar.type, ar.created_at::text
            FROM approval_requests ar
            JOIN users u ON u.id = ar.user_id
            WHERE ar.status = 'pending'
            ORDER BY ar.created_at ASC
            """
        )
    ).fetchall()

    return [
        PendingApprovalRow(
            request_id=int(r[0]),
            user_id=int(r[1]),
            user_email=str(r[2]),
            from_stage_id=int(r[3]),
            to_stage_id=(int(r[4]) if r[4] is not None else None),
            type=str(r[5]),
            created_at=str(r[6]),
        )
        for r in rows
    ]


@dataclass(frozen=True)
class ApproveResult:
    request_id: int
    status: str
    user_id: int
    from_stage_id: int
    to_stage_id: Optional[int]


def approve_rank_transition(
    db: Session, *, request_id: int, admin_id: int, comment: str | None
) -> ApproveResult:
    # 1) атомарно переводим request из pending -> approved
    row = db.execute(
        text(
            """
            UPDATE approval_requests
            SET status='approved',
                approved_at=now(),
                approved_by_admin_id=:aid,
                comment=COALESCE(:comment, comment)
            WHERE id=:rid AND status='pending'
            RETURNING user_id, from_stage_id, to_stage_id, type
            """
        ),
        {"rid": request_id, "aid": admin_id, "comment": comment},
    ).fetchone()

    if row is None:
        # либо не существует, либо уже не pending
        exists = db.execute(text("SELECT 1 FROM approval_requests WHERE id=:rid"), {"rid": request_id}).fetchone()
        if exists is None:
            raise ApprovalNotFound("Заявка не найдена")
        raise ApprovalAlreadyProcessed("Заявка уже обработана")

    user_id = int(row[0])
    from_stage_id = int(row[1])
    to_stage_id = row[2]
    req_type = str(row[3])

    if req_type != "rank_transition":
        raise ApprovalInvalid("Этот approve предназначен только для rank_transition")

    if to_stage_id is None:
        raise ApprovalInvalid("У заявки не задана целевая стадия to_stage_id")

    to_stage_id = int(to_stage_id)

    # 2) берём settings_version_id с текущей стадии (замораживаем одну версию настроек в рамках траектории)
    sv_row = db.execute(
        text(
            """
            SELECT settings_version_id
            FROM user_stage_progress
            WHERE user_id=:uid AND stage_id=:sid
            FOR UPDATE
            """
        ),
        {"uid": user_id, "sid": from_stage_id},
    ).fetchone()
    if sv_row is None:
        raise ApprovalInvalid("Нет записи user_stage_progress для from_stage")

    settings_version_id = int(sv_row[0])

    # 3) завершаем from_stage (pending_approval -> completed)
    db.execute(
        text(
            """
            UPDATE user_stage_progress
            SET status='completed',
                completed_at=COALESCE(completed_at, now())
            WHERE user_id=:uid AND stage_id=:sid
            """
        ),
        {"uid": user_id, "sid": from_stage_id},
    )

    # 4) активируем to_stage как active (инвариант: единственная active стадия обеспечит БД)
    db.execute(
        text(
            """
            INSERT INTO user_stage_progress(user_id, stage_id, settings_version_id, status, activated_at, completed_at)
            VALUES (:uid, :tsid, :sv, 'active', now(), NULL)
            ON CONFLICT (user_id, stage_id)
            DO UPDATE SET
              status='active',
              settings_version_id=EXCLUDED.settings_version_id,
              activated_at=COALESCE(user_stage_progress.activated_at, now()),
              completed_at=NULL
            """
        ),
        {"uid": user_id, "tsid": to_stage_id, "sv": settings_version_id},
    )

    return ApproveResult(
        request_id=request_id,
        status="approved",
        user_id=user_id,
        from_stage_id=from_stage_id,
        to_stage_id=to_stage_id,
    )