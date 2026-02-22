from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from adaptive_learning_platform.api.deps import current_user_id, get_db
from adaptive_learning_platform.api.v1.progress.schemas import CurrentStageResponse
from adaptive_learning_platform.application.services.progress_service import (
    NoActiveStageError,
    get_current_stage,
)
from adaptive_learning_platform.api.v1.progress.eligibility_schemas import EligibilityReportOut, MissingArticleOut
from adaptive_learning_platform.application.services.eligibility_service import EligibilityError, get_level_exam_eligibility
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException

router = APIRouter()


@router.get(
    "/current-stage",
    response_model=CurrentStageResponse,
    summary="Текущая активная стадия пользователя (protected)",
)
def current_stage(
    db: Session = Depends(get_db),
    user_id: int = Depends(current_user_id),
) -> CurrentStageResponse:
    try:
        cs = get_current_stage(db, user_id=user_id)
        return CurrentStageResponse(
            user_id=cs.user_id,
            track_id=cs.track_id,
            track_name=cs.track_name,
            stage_id=cs.stage_id,
            rank=cs.rank,
            level=cs.level,
            status=cs.status,
            activated_at=cs.activated_at,
            settings_version_id=cs.settings_version_id,
        )
    except NoActiveStageError:
        raise HTTPException(status_code=404, detail="Активная стадия пользователя не найдена")

@router.get(
    "/eligibility",
    response_model=EligibilityReportOut,
    summary="Допуск к level-exam на текущей стадии (отчёт + незакрытые элементы)",
)
def eligibility(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> EligibilityReportOut:
    try:
        rep = get_level_exam_eligibility(db, user_id=user_id)
        return EligibilityReportOut(
            user_id=rep.user_id,
            stage_id=rep.stage_id,
            rank=rep.rank,
            level=rep.level,
            settings_version_id=rep.settings_version_id,
            required_total=rep.required_total,
            required_done=rep.required_done,
            optional_total=rep.optional_total,
            optional_done=rep.optional_done,
            missing_required=[MissingArticleOut(**m.__dict__) for m in rep.missing_required],
            missing_optional=[MissingArticleOut(**m.__dict__) for m in rep.missing_optional],
            eligible=rep.eligible,
        )
    except EligibilityError as e:
        raise HTTPException(status_code=412, detail=str(e))