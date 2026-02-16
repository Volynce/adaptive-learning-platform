from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Проверка доступности модуля exams")
def health_check() -> dict:
    return {"status": "ok", "module": "exams"}
