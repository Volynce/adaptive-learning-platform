from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

# Важно: используем настройки проекта (они читают .env).
# Это обеспечивает единый источник истины для DATABASE_URL.
from adaptive_learning_platform.config.settings import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# На Step-06 моделей ещё нет, поэтому metadata отсутствует.
# Это сознательное решение: миграции пишем вручную, автогенерацию не используем.
target_metadata = None


def _get_database_url() -> str:
    """
    Получаем DATABASE_URL через Settings.

    Почему так:
    - .env подхватывается автоматически (через pydantic-settings),
    - один источник правды для приложения и миграций,
    - меньше рассогласований между окружениями.
    """
    settings = get_settings()
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    """
    Offline режим: генерируем SQL без подключения к БД.
    """
    url = _get_database_url()
    context.configure(
        url=url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # В проекте придерживаемся явных миграций, поэтому compare_* не используем.
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Online режим: применяем миграции с подключением к БД.

    Принцип устойчивости:
    - engine создаётся здесь локально,
    - pool.NullPool исключает “залипание” соединений в контексте миграций.
    """
    url = _get_database_url()

    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Ручные миграции: no autogenerate. Это правило закреплено в decision log.
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
