import asyncio
import logging
import time
from collections.abc import Awaitable
from ..schemas.common import ResultBase
from ..schemas.common import DiagnosticStatus

from ..schemas.responses import DiagnosticRunResult
from ..services.dns_service import resolve_dns
from ..services.http_service import check_http
from ..services.ping_service import ping_host
from ..services.port_service import check_port

logger = logging.getLogger(__name__)

async def run_diagnostics(
        host: str,
        port: int | None = None,
        url: str | None = None,
        ping_count: int = 4,
        timeout: float = 3.0,
) -> DiagnosticRunResult:
    start = time.perf_counter()

    tasks: dict[str, Awaitable[ResultBase]] = {
        "ping": ping_host(
            host,
            count=ping_count,
            timeout=timeout,
        ),
        "dns": resolve_dns(host),
    }

    if port is not None:
        tasks["port"] = check_port(
            host,
            port,
            timeout=timeout,
        )

    if url is not None:
        tasks["http"] = check_http(
            str(url),
            timeout=timeout,
        )

    results = dict(zip(tasks.keys(), await asyncio.gather(*tasks.values())))
    duration_ms = (time.perf_counter() - start) * 1000

    checks_run = list(results.values())
    overall_status = DiagnosticStatus.SUCCESS if all(r.status == "success" for r in checks_run) else DiagnosticStatus.ERROR

    logger.info("Diagnostic run for %s completed in %.1fms (overall_status=%s)", host, duration_ms, overall_status)

    return DiagnosticRunResult(
        target=host,
        ping=results["ping"],
        dns=results["dns"],
        port=results.get("port"),
        http=results.get("http"),
        status=overall_status,
        duration_ms=round(duration_ms, 2),
    )