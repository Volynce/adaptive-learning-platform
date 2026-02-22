from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from adaptive_learning_platform.api.deps import current_admin_id, get_db
from adaptive_learning_platform.api.v1.admin.schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    ApproveRequestIn,
    ApproveResponseOut,
    PendingApprovalOut,
)
from adaptive_learning_platform.application.services.admin_auth_service import (
    AdminInactive,
    AdminNotFound,
    InvalidAdminCredentials,
    admin_login,
)
from adaptive_learning_platform.application.services.admin_approvals_service import (
    ApprovalAlreadyProcessed,
    ApprovalInvalid,
    ApprovalNotFound,
    approve_rank_transition,
    list_pending_approvals,
)

router = APIRouter()


@router.post(
    "/login",
    response_model=AdminLoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Логин администратора (JWT access-only)",
)
def admin_login_endpoint(payload: AdminLoginRequest, db: Session = Depends(get_db)) -> AdminLoginResponse:
    try:
        res = admin_login(db, email=payload.email, password=payload.password)
        db.commit()
        return AdminLoginResponse(access_token=res.access_token)
    except (AdminNotFound, InvalidAdminCredentials) as e:
        db.rollback()
        raise HTTPException(status_code=401, detail=str(e))
    except AdminInactive as e:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(e))
    except Exception:
        db.rollback()
        raise


@router.get(
    "/approvals/pending",
    response_model=list[PendingApprovalOut],
    summary="Список заявок на подтверждение (pending)",
)
def pending_approvals(db: Session = Depends(get_db), admin_id: int = Depends(current_admin_id)) -> list[PendingApprovalOut]:
    _ = admin_id
    rows = list_pending_approvals(db)
    return [PendingApprovalOut(**r.__dict__) for r in rows]


@router.post(
    "/approvals/{request_id}/approve",
    response_model=ApproveResponseOut,
    summary="Подтвердить rank_transition (pending -> approved) и активировать следующую стадию",
)
def approve(
    request_id: int,
    payload: ApproveRequestIn,
    db: Session = Depends(get_db),
    admin_id: int = Depends(current_admin_id),
) -> ApproveResponseOut:
    try:
        res = approve_rank_transition(db, request_id=request_id, admin_id=admin_id, comment=payload.comment)
        db.commit()
        return ApproveResponseOut(**res.__dict__)
    except ApprovalNotFound as e:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except ApprovalAlreadyProcessed as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    except ApprovalInvalid as e:
        db.rollback()
        raise HTTPException(status_code=412, detail=str(e))
    except Exception:
        db.rollback()
        raise