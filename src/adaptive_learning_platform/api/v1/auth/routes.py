from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from adaptive_learning_platform.api.deps import get_db
from adaptive_learning_platform.api.v1.auth.schemas import SignupRequest, SignupResponse
from adaptive_learning_platform.application.services.auth_service import (
    EmailAlreadyExists,
    MissingBootstrapData,
    signup,
)

router = APIRouter()


@router.get("/health", summary="Проверка доступности модуля auth")
def health_check() -> dict:
    return {"status": "ok", "module": "auth"}


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя (email + password)",
)
def signup_endpoint(payload: SignupRequest, db: Session = Depends(get_db)) -> SignupResponse:
    try:
        result = signup(db, email=payload.email, full_name=payload.full_name, password=payload.password)
        db.commit()
        return SignupResponse(id=result.user_id, email=result.email, full_name=result.full_name)
    except EmailAlreadyExists:
        db.rollback()
        raise HTTPException(status_code=409, detail="Пользователь с таким email уже существует")
    except MissingBootstrapData as e:
        db.rollback()
        raise HTTPException(status_code=412, detail=str(e))
    except Exception:
        db.rollback()
        raise

@router.get("/health", summary="Проверка доступности модуля auth")
def health_check() -> dict:
    return {"status": "ok", "module": "auth"}


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя (email + password)",
)
def signup_endpoint(payload: SignupRequest, db: Session = Depends(get_db)) -> SignupResponse:
    try:
        result = signup(db, email=payload.email, full_name=payload.full_name, password=payload.password)
        db.commit()
        return SignupResponse(id=result.user_id, email=result.email, full_name=result.full_name)
    except EmailAlreadyExists:
        db.rollback()
        raise HTTPException(status_code=409, detail="Пользователь с таким email уже существует")
    except MissingBootstrapData as e:
        db.rollback()
        raise HTTPException(status_code=412, detail=str(e))
    except Exception:
        db.rollback()
        raise