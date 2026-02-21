from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from adaptive_learning_platform.api.deps import current_user_id, get_db
from adaptive_learning_platform.api.v1.diagnostika.schemas import (
    StartDiagnostikaResponse,
    SubmitDiagnostikaRequest,
    SubmitDiagnostikaResponse,
    QuestionOut,
    AnswerOptionOut,
    ModuleStatOut,
)
from adaptive_learning_platform.application.services.diagnostika_service import (
    DiagnostikaAlreadyExists,
    NotTraineeStage,
    NotEnoughQuestions,
    AlreadySubmitted,
    start_diagnostika,
    submit_diagnostika,
)

router = APIRouter()


@router.post(
    "/start",
    response_model=StartDiagnostikaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Старт входной диагностики (только Trainee_0, один раз)",
)
def start(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> StartDiagnostikaResponse:
    try:
        res = start_diagnostika(db, user_id=user_id)
        db.commit()
        return StartDiagnostikaResponse(
            diagnostika_id=res.diagnostika_id,
            total_q=res.total_q,
            questions=[
                QuestionOut(
                    id=q.id,
                    text=q.text,
                    options=[AnswerOptionOut(id=o.id, pos=o.pos, text=o.text) for o in q.options],
                )
                for q in res.questions
            ],
        )
    except DiagnostikaAlreadyExists:
        db.rollback()
        raise HTTPException(status_code=409, detail="Диагностика уже была пройдена")
    except NotTraineeStage as e:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(e))
    except NotEnoughQuestions as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    except Exception:
        db.rollback()
        raise


@router.post(
    "/submit",
    response_model=SubmitDiagnostikaResponse,
    summary="Отправка ответов входной диагностики",
)
def submit(payload: SubmitDiagnostikaRequest, db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> SubmitDiagnostikaResponse:
    try:
        res = submit_diagnostika(
            db,
            user_id=user_id,
            diagnostika_id=payload.diagnostika_id,
            answers=[a.model_dump() for a in payload.answers],
        )
        db.commit()
        return SubmitDiagnostikaResponse(
            diagnostika_id=res.diagnostika_id,
            total_q=res.total_q,
            score_total=res.score_total,
            module_stats=[ModuleStatOut(module_id=m.module_id, correct_cnt=m.correct_cnt, total_cnt=m.total_cnt) for m in res.module_stats],
        )
    except AlreadySubmitted:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ответы уже были отправлены ранее")
    except Exception:
        db.rollback()
        raise