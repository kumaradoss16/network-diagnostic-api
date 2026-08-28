import asyncio
import logging
import socket
import time

from ..schemas.responses import DNSResult
from ..schemas.common import DiagnosticStatus

logger = logging.getLogger(__name__)

def _resolve_sync(hostname: str) -> list[str]:
    infos = socket.getaddrinfo(hostname, None)
    seen: dict[str, None] = {}
    for info in infos:
        ip = info[4][0]
        seen.setdefault(ip, None)
    return list(seen.keys())

async def resolve_dns(hostname: str) -> DNSResult:
    start = time.perf_counter()
    loop = asyncio.get_running_loop()
    try:
        ip_addresses = await loop.run_in_executor(None, _resolve_sync, hostname)
        duration_ms = (time.perf_counter() - start) * 1000
        return DNSResult(
            hostname=hostname,
            ip_addresses=ip_addresses,
            resolution_time_ms=round(duration_ms, 2),
            status=DiagnosticStatus.SUCCESS,
            duration_ms=round(duration_ms, 2),
        )
    except socket.gaierror as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info("DNS resolution failed for %s: %s", hostname, exc)
        return DNSResult(
            hostname=hostname,
            ip_addresses=[],
            resolution_time_ms=round(duration_ms, 2),
            status=DiagnosticStatus.ERROR,
            duration_ms=round(duration_ms, 2),
            error=f"DNS resolution failed: {exc.strerror if hasattr(exc, 'strerror') else str(exc)}"
        )