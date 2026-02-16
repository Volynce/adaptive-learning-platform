from fastapi import FastAPI

from adaptive_learning_platform.api.router import api_router


def create_app() -> FastAPI:
    """
    Фабрика приложения.

    Принцип: сборка приложения должна быть одинаковой для local/test/prod.
    На старте запрещено выполнять миграции/сидинг/DDL и любые побочные эффекты.
    """
    app = FastAPI(
        title="Adaptive Learning Platform API",
        version="0.1.0",
    )

    # Подключаем единый роутер API (дальше внутри подключается /api/v1).
    app.include_router(api_router)

    return app


# Экспорт для ASGI-сервера (uvicorn) и интеграционных тестов.
app = create_app()
