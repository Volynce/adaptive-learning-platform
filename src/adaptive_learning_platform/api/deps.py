from __future__ import annotations

from adaptive_learning_platform.config.settings import Settings, get_settings


def settings_dep() -> Settings:
    """
    Dependency для FastAPI.

    Сейчас:
    - отдаём типизированные настройки из единого источника (pydantic-settings).

    Позже (в следующих шагах):
    - здесь появится dependency для db session (get_db),
    - а также current_user/current_admin для авторизации.
    """
    return get_settings()
