from fastapi import APIRouter  # allows you to organize FastAPI endpoints into separate modules

from ..core.config import get_settings
from ..schemas.common import HealthResponse

# Creates an API router.
router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse, summary="Liveness check")
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", app_name=settings.APP_NAME, version=settings.APP_VERSION)
