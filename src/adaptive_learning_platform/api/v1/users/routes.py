from fastapi import APIRouter, Depends

from adaptive_learning_platform.api.deps import current_user

router = APIRouter()


@router.get("/me", summary="Текущий пользователь (protected)")
def me(user: dict = Depends(current_user)) -> dict:
    return user