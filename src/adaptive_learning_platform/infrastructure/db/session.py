from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from adaptive_learning_platform.config.settings import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """
    Единая точка создания Engine.

    Важно:
    - DATABASE_URL берём только из Settings (env/.env).
    - Engine создаём лениво (через cache), чтобы импорт модулей не падал “раньше времени”.
    """
    settings = get_settings()
    return create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        future=True,
    )


@lru_cache(maxsize=1)
def get_sessionmaker() -> sessionmaker:
    """
    Единая точка создания sessionmaker.
    """
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )


def get_session() -> Generator[Session, None, None]:
    """
    Dependency-генератор сессии для FastAPI.
    """
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Контекст транзакции для application/use-case слоя (позже будем использовать системно).
    """
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def ping_db(db: Session) -> None:
    """
    Техническая проверка доступности БД.
    """
    db.execute(text("SELECT 1"))