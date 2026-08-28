"""HTTP/HTTPS connectivity check service."""
import logging
import time
from http.client import responses

import httpx

from ..schemas.responses import HTTPCheckResult
from ..schemas.common import DiagnosticStatus

logger = logging.getLogger(__name__)

async def check_http(url: str, timeout: float = 5.0, follow_redirects: bool = True) -> HTTPCheckResult:
    start = time.perf_counter()
    try:
        # Creates an asynchronous HTTP client
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=follow_redirects) as client:
            response = await client.get(url)   # Sends an asynchronous HTTP GET request
        duration_ms = (time.perf_counter() - start) * 1000
        final_url = str(response.url)
        return HTTPCheckResult(
            url=url,
            status_code=response.status_code,
            is_reachable=True,
            response_time_ms=round(duration_ms, 2),
            final_url=final_url if final_url != url else None,
            status=DiagnosticStatus.SUCCESS,
            duration_ms=round(duration_ms, 2),
        )
    except httpx.TimeoutException:
        duration_ms = (time.perf_counter() - start) * 1000
        return HTTPCheckResult(
            url=url,
            status_code=None,
            is_reachable=False,
            response_time_ms=round(duration_ms, 2),
            status=DiagnosticStatus.ERROR,
            duration_ms=round(duration_ms, 2),
            error=f"Request to {url} time out after {timeout}s.",
        )
    except httpx.RequestError as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info("HTTP check failed for %s: %s", url, exc)
        return HTTPCheckResult(
            url=url,
            status_code=None,
            is_reachable=False,
            response_time_ms=round(duration_ms, 2),
            status=DiagnosticStatus.ERROR,
            duration_ms=round(duration_ms, 2),
            error=str(exc),
        )

