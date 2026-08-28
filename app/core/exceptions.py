from datetime import datetime, timezone
import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class NetworkDiagnosticError(Exception):
    def __init__(self, message: str, code: str = "DIAGNOSTIC_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class BlockedTargetError(NetworkDiagnosticError):
    def __init__(self, target: str):
        super().__init__(
            message=(
                f"Target '{target}' resolves to a private, loopback, or "
                "reserved address, which is not permitted by this server's "
                "configuration."
            ),
            code="BLOCKED_TARGET",
        )

# Creates the common JSON structure used by every error handler.
def _error_envelope(code: str, message: str, details=None) -> dict:
    return {
        "success": False,
        "error": {"code": code, "message": message, "details": details},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# Attach all custom exception handlers to the FastAPI app.
def register_exception_handlers(app: FastAPI) -> None:
    # After registration, FastAPI knows which function to call for each exception type.
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Log the validation error
        logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
        safe_details = jsonable_encoder(exc.errors(), custom_encoder={Exception: str})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_envelope(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=safe_details
            )
        )

    @app.exception_handler(NetworkDiagnosticError)
    async  def diagnostic_error_handler(request: Request, exc: NetworkDiagnosticError):
        logger.info("Diagnostic error on %s %: %s", request.method, request.url.path, exc.message)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_error_envelope(code=exc.code, message=exc.message)
        )


    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_envelope(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred. Please try again later.",
            ),
        )




