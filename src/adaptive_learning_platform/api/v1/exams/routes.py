from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from adaptive_learning_platform.api.deps import current_user_id, get_db
from adaptive_learning_platform.api.v1.exams.schemas import StartLevelExamResponse, ExamQuestionOut, AnswerOptionOut
from adaptive_learning_platform.application.services.level_exam_service import (
    AlreadyPassed,
    NotEligible,
    NotEnoughQuestions,
    start_level_exam,
)

router = APIRouter()


@router.get("/health", summary="Проверка доступности модуля exams")
def health_check() -> dict:
    return {"status": "ok", "module": "exams"}


@router.post(
    "/level/start",
    response_model=StartLevelExamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Старт попытки level-exam (только при допуске)",
)
def start_level(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> StartLevelExamResponse:
    try:
        res = start_level_exam(db, user_id=user_id)
        db.commit()
        return StartLevelExamResponse(
            attempt_id=res.attempt_id,
            attempt_no=res.attempt_no,
            total_q=res.total_q,
            questions=[
                ExamQuestionOut(
                    id=q.id,
                    text=q.text,
                    options=[AnswerOptionOut(id=o.id, pos=o.pos, text=o.text) for o in q.options],
                )
                for q in res.questions
            ],
        )
    except NotEligible as e:
        db.rollback()
        # Возвращаем 412 + отчёт (как фиксированное правило шага)
        r = e.report
        raise HTTPException(
            status_code=412,
            detail={
                "message": "Недопуск к level-exam",
                "eligibility": {
                    "required_total": r.required_total,
                    "required_done": r.required_done,
                    "optional_total": r.optional_total,
                    "optional_done": r.optional_done,
                    "missing_required": [m.__dict__ for m in r.missing_required],
                    "missing_optional": [m.__dict__ for m in r.missing_optional],
                    "eligible": r.eligible,
                },
            },
        )
    except AlreadyPassed as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    except NotEnoughQuestions as e:
        db.rollback()
        raise HTTPException(status_code=412, detail=str(e))
    except Exception:
        db.rollback()
        raise

