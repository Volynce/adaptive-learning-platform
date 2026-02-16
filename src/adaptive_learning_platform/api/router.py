from fastapi import APIRouter

from adaptive_learning_platform.api.v1.router import v1_router

api_router = APIRouter()

# Единая точка подключения версий API.
api_router.include_router(v1_router)
