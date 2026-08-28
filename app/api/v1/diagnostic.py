import logging
from fastapi import APIRouter, status

from ...core.config import get_settings
from ...core.exceptions import BlockedTargetError
from ...schemas.requests import (
    DiagnosticRunRequest,
    DNSRequest,
    HTTPCheckRequest,
    LatencyRequest,
    PingRequest,
    PortCheckRequest,
)
from ...schemas.responses import (
    DiagnosticRunResult,
    DNSResult,
    HTTPCheckResult,
    LatencyResult,
    PingResult,
    PortCheckResult
)

from ...services.diagnostic_service import run_diagnostics
from ...services.dns_service import resolve_dns
from ...services.http_service import check_http
from ...services.latency_service import measure_latency
from ...services.ping_service import ping_host
from ...services.port_service import check_port
from ...utils.validators import is_private_or_reserved

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/diagnostics", tags=["Diagnostics"])

# Private helper function
def _enforce_target_policy(target: str) -> None:
    settings = get_settings()
    if settings.BLOCK_PRIVATE_TARGETS and is_private_or_reserved(target):
        raise BlockedTargetError(target)


@router.post(
    "/ping",
    response_model=PingResult,
    status_code=status.HTTP_200_OK,
    summary="Ping a host and measure round-trip latency.",
)
async def ping(request: PingRequest) -> PingResult:
    _enforce_target_policy(request.host)
    logger.info("Ping requested: host=%s count=%s", request.host, request.count)
    return await ping_host(request.host, count=request.count, timeout=request.timeout)


@router.post(
    "/dns",
    response_model=DNSResult,
    status_code=status.HTTP_200_OK,
    summary="Resolve a hostname to its IP addresses",
)
async def dns_lookup(request: DNSRequest) -> DNSResult:
    logger.info("DNS lookup requested: hostname=%s", request.hostname)
    return await resolve_dns(request.hostname)


@router.post(
    "/port",
    response_model=PortCheckResult,
    status_code=status.HTTP_200_OK,
    summary="Check whether a TCP port is open on a host",
)
async def port_check(request: PortCheckRequest) -> PortCheckResult:
    _enforce_target_policy(request.host)
    logger.info("Port check requested: host=%s port=%s", request.host, request.port)
    return await check_port(request.host, request.port, timeout=request.timeout)


@router.post(
    "/http",
    response_model=HTTPCheckResult,
    status_code=status.HTTP_200_OK,
    summary="Check HTTP/HTTPS connectivity to a URL.",
)
async def http_check(request: HTTPCheckRequest) -> HTTPCheckResult:
    _enforce_target_policy(request.url.host)
    logger.info("HTTP check requested: url=%s timeout=%s", request.url, request.timeout)
    return await check_http(str(request.url), timeout=request.timeout, follow_redirects=request.follow_redirects)


@router.post(
    "/latency",
    response_model=LatencyResult,
    status_code=status.HTTP_200_OK,
    summary="Measure latency and jiter to a host over multiple samples.",
)
async def latency(request: LatencyRequest) -> LatencyResult:
    _enforce_target_policy(request.host)
    logger.info("Latency measurement requested: host=%s count=%s", request.host, request.count)
    return await measure_latency(request.host, count=request.count, timeout=request.timeout)


@router.post(
    "/run",
    response_model=DiagnosticRunResult,
    status_code=status.HTTP_200_OK,
    summary="Run a combined diagnostic (ping + DNS, plus port/HTTP if provided)",
)
async def run(request: DiagnosticRunRequest) -> DiagnosticRunResult:
    _enforce_target_policy(request.host)
    if request.url is not None:
        _enforce_target_policy(request.url.host)
    logger.info("Combined diagnostic run requested: host=%s port=%s url=%s", request.host, request.port, request.url,)
    return await run_diagnostics(
        host=request.host,
        port=request.port,
        url=request.url,
        ping_count=request.ping_count,
        timeout=request.timeout
    )
