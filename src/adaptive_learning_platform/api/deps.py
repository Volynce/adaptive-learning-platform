from __future__ import annotations

from typing import Generator

from sqlalchemy.orm import Session

from adaptive_learning_platform.config.settings import Settings, get_settings
from adaptive_learning_platform.infrastructure.db.session import get_session


def settings_dep() -> Settings:
    """
    Dependency для FastAPI.

    Сейчас:
    - отдаём типизированные настройки из единого источника (pydantic-settings).

    Позже (в следующих шагах):
    - здесь появится dependency для current_user/current_admin для авторизации.
    """
    return get_settings()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency для выдачи SQLAlchemy Session.

    Важно:
    - это generator-функция (yield), иначе FastAPI передаст generator-объект,
      и попытка вызвать db.execute(...) завершится ошибкой.
    """
    yield from get_session()