"""Defines shared Pydantic models for a network diagnostic API"""

from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field

class DiagnosticStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"

class ResultBase(BaseModel):
    status: DiagnosticStatus
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: float = Field(..., description="Total time the check took to run, in milliseconds.")
    error: str | None = Field(default=None, description="Human-readable error detail when status is 'error'.")

# This Model describes an API-level error
class ErrorDetail(BaseModel):
    code: str
    message: str
    details: object | None = None

# Defines the complete response returned when the API request fails.
class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Defines the response for a health-check endpoint
class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str
    version: str
    timestamp: datetime = Field(default_factory=lambda : datetime.now(timezone.utc))