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
from adaptive_learning_platform.api.v1.content.schemas import (
    GetMinitestResponse,
    MinitestQuestionOut,
    AnswerOptionOut,
    SubmitMinitestRequest,
    SubmitMinitestResponse,
)
from adaptive_learning_platform.application.services.minitest_service import (
    ArticleNotAssigned,
    NotRequiredArticle,
    MinitestNotConfigured,
    MinitestError,
    get_minitest,
    submit_minitest,
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

@router.get(
    "/{article_id}/minitest",
    response_model=GetMinitestResponse,
    summary="Получить мини-тест (3 вопроса) для required статьи",
)
def api_get_minitest(article_id: int, db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> GetMinitestResponse:
    try:
        res = get_minitest(db, user_id=user_id, article_id=article_id)
        return GetMinitestResponse(
            article_id=res.article_id,
            questions=[
                MinitestQuestionOut(
                    id=q.id,
                    text=q.text,
                    options=[AnswerOptionOut(id=o.id, pos=o.pos, text=o.text) for o in q.options],
                )
                for q in res.questions
            ],
        )
    except (ArticleNotAssigned, NotRequiredArticle) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except MinitestNotConfigured as e:
        raise HTTPException(status_code=412, detail=str(e))


@router.post(
    "/{article_id}/minitest/submit",
    response_model=SubmitMinitestResponse,
    summary="Отправить ответы мини-теста; PASS только при 3/3",
)
def api_submit_minitest(article_id: int, payload: SubmitMinitestRequest, db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> SubmitMinitestResponse:
    try:
        res = submit_minitest(
            db,
            user_id=user_id,
            article_id=article_id,
            answers=[a.model_dump() for a in payload.answers],
        )
        db.commit()
        return SubmitMinitestResponse(
            article_id=res.article_id,
            passed=res.passed,
            correct_cnt=res.correct_cnt,
            total_cnt=res.total_cnt,
        )
    except (ArticleNotAssigned, NotRequiredArticle) as e:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(e))
    except (MinitestNotConfigured, MinitestError) as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        db.rollback()
        raise