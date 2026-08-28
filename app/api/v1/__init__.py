from fastapi import APIRouter   # creating and organizing API routes
from .diagnostic import router as diagnostic_router

router = APIRouter()   # router as a container for related endpoints.
router.include_router(diagnostic_router)   # Add all routes from diagnostics_router to this router