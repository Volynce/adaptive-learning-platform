from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Типизированная конфигурация приложения.

    Правило проекта:
    - Источник истины — переменные окружения (и .env только для локальной разработки).
    - Подключение к БД задаётся ТОЛЬКО через DATABASE_URL.
    - Конфигурация не должна читаться разрозненно через os.environ по коду.
    """

    model_config = SettingsConfigDict(
        env_file=".env",          # локальный файл окружения (не коммитится)
        env_file_encoding="utf-8",
        extra="ignore",           # лишние переменные окружения не ломают запуск
    )

    # --- Общие параметры приложения ---
    APP_ENV: Literal["local", "test", "prod"] = Field(
        default="local",
        description="Среда запуска приложения (local/test/prod).",
    )
    APP_DEBUG: bool = Field(
        default=True,
        description="Флаг отладочного режима (для local обычно True).",
    )

    # --- База данных ---
    DATABASE_URL: str = Field(
        ...,
        description="Строка подключения к БД. Единственный поддерживаемый формат конфигурации БД.",
    )

    # --- JWT (dev/MVP: access-only) ---
    JWT_SECRET: str = Field(
        ...,
        description="Секрет для подписи JWT (хранить только в .env, не коммитить).",
    )
    JWT_ALG: str = Field(
        default="HS256",
        description="Алгоритм подписи JWT.",
    )
    JWT_ACCESS_TTL_MINUTES: int = Field(
        default=60,
        description="Время жизни access-токена в минутах.",
    )

    # --- Хеширование паролей ---
    PWD_HASH_SCHEME: str = Field(
        default="bcrypt",
        description="Алгоритм хеширования паролей (на учебном этапе bcrypt).",
    )
    PWD_BCRYPT_ROUNDS: int = Field(
        default=12,
        description="Стоимость bcrypt (количество раундов).",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Единая точка получения Settings.

    Зачем cache:
    - настройки не должны пересоздаваться на каждый запрос;
    - гарантируется единообразие конфигурации внутри процесса.
    """
    return Settings()
