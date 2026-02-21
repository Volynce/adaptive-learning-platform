from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from adaptive_learning_platform.api.deps import current_user_id, get_db
from adaptive_learning_platform.api.v1.content.schemas import AssignContentResponse, AssignedArticleOut
from adaptive_learning_platform.application.services.content_service import (
    AlreadyAssigned,
    MissingDiagnostika,
    MissingArticles,
    NotTraineeStage,
    WrongArticleKind,
    assign_content_for_current_stage,
    list_my_stage_articles,
    mark_optional_read,
)

router = APIRouter()


@router.get("/health", summary="Проверка доступности модуля content")
def health_check() -> dict:
    return {"status": "ok", "module": "content"}


@router.post(
    "/assign",
    response_model=AssignContentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Назначить контент на текущую стадию (по слабым модулям)",
)
def assign(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> AssignContentResponse:
    try:
        res = assign_content_for_current_stage(db, user_id=user_id)
        db.commit()
        return AssignContentResponse(**res)
    except AlreadyAssigned as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    except MissingDiagnostika as e:
        db.rollback()
        raise HTTPException(status_code=412, detail=str(e))
    except (MissingArticles, NotTraineeStage) as e:
        db.rollback()
        raise HTTPException(status_code=412, detail=str(e))
    except Exception:
        db.rollback()
        raise


@router.get(
    "/my",
    response_model=list[AssignedArticleOut],
    summary="Мои назначенные статьи на текущей стадии",
)
def my(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> list[AssignedArticleOut]:
    items = list_my_stage_articles(db, user_id=user_id)
    return [AssignedArticleOut(**i.__dict__) for i in items]


@router.post(
    "/{article_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отметить optional статью как прочитанную",
)
def mark_read(article_id: int, db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> None:
    try:
        mark_optional_read(db, user_id=user_id, article_id=article_id)
        db.commit()
        return None
    except WrongArticleKind as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))