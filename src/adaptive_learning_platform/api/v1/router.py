from fastapi import APIRouter

from adaptive_learning_platform.api.v1.auth.routes import router as auth_router
from adaptive_learning_platform.api.v1.catalog.routes import router as catalog_router
from adaptive_learning_platform.api.v1.content.routes import router as content_router
from adaptive_learning_platform.api.v1.exams.routes import router as exams_router
from adaptive_learning_platform.api.v1.approvals.routes import router as approvals_router
from adaptive_learning_platform.api.v1.settings.routes import router as settings_router
from adaptive_learning_platform.api.v1.health.routes import router as health_router
from adaptive_learning_platform.api.v1.users.routes import router as users_router

v1_router = APIRouter(prefix="/api/v1")

# Подключение модульных роутеров (пока заглушки, но структура и контракты готовы).
v1_router.include_router(auth_router, prefix="/auth", tags=["auth"])
v1_router.include_router(catalog_router, prefix="/catalog", tags=["catalog"])
v1_router.include_router(content_router, prefix="/content", tags=["content"])
v1_router.include_router(exams_router, prefix="/exams", tags=["exams"])
v1_router.include_router(approvals_router, prefix="/approvals", tags=["approvals"])
v1_router.include_router(settings_router, prefix="/settings", tags=["settings"])
v1_router.include_router(health_router, prefix="/health", tags=["health"])
v1_router.include_router(users_router, prefix="/users", tags=["users"])
