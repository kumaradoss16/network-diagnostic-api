import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware   # It controls which browser-based applications are allowed to make requests to your API from another origin.

from .api import api_router
from .core.config import get_settings
from .core.exceptions import register_exception_handlers
from .core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


# Responsible for application startup and shutdown events.
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "%s v%s starting up (environment=%s, block_private_targets=%s)",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
        settings.BLOCK_PRIVATE_TARGETS,
    )
    yield
    logger.info("%s shutting down", settings.APP_NAME)


# Creates the actual FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "A learning-focused backend project exposing common network "
        "diagnostics (ping, DNS lookup, TCP port check, HTTP/HTTPS "
        "connectivity, latency measurement) as a REST API."
    ),
    lifespan=lifespan,
)

# Adds CORS middleware to your FastAPI application
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Attaches custom exception handlers to the FastAPI application
register_exception_handlers(app)
# connects all API routes to the FastAPI application
app.include_router(api_router)