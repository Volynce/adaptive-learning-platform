from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from adaptive_learning_platform.api.deps import current_user_id, get_db
from adaptive_learning_platform.api.v1.progress.schemas import CurrentStageResponse
from adaptive_learning_platform.application.services.progress_service import (
    NoActiveStageError,
    get_current_stage,
)

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