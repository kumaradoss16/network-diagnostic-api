from fastapi import APIRouter
from .health import router as health_router
from .v1 import router as v1_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(v1_router)