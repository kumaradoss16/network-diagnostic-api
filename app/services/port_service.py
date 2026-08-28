import asyncio
import logging
import time

from ..schemas.responses import PortCheckResult
from ..schemas.common import DiagnosticStatus

logger = logging.getLogger(__name__)

async def check_port(host: str, port: int, timeout: float = 3.0) -> PortCheckResult:
    start = time.perf_counter()
    writer = None   # Only need to establish and close the connection

    try:
        """
        reader - receive the date
        writer - send the data or close the connection.
        wait_for() - as waiting for an awaitable with a timeout and cancelling it if the timeout expires.
        """
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        duration_ms = (time.perf_counter() - start) * 1000
        return PortCheckResult(
            host=host,
            port=port,
            is_open=True,
            response_time_ms=round(duration_ms, 2),
            status=DiagnosticStatus.SUCCESS,
            duration_ms=round(duration_ms, 2),
        )
    except asyncio.TimeoutError:
        duration_ms = (time.perf_counter() - start) * 1000
        return PortCheckResult(
            host=host,
            port=port,
            is_open=False,
            response_time_ms=round(duration_ms, 2),
            status=DiagnosticStatus.ERROR,
            duration_ms=round(duration_ms, 2),
            error=f"Connection to {host}:{port} time out after {timeout}s."
        )
    except (ConnectionRefusedError, OSError) as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info("Port check failed for %s %s: %s", host, port, exc)
        return PortCheckResult(
            host=host,
            port=port,
            is_open=False,
            response_time_ms=round(duration_ms, 2),
            status=DiagnosticStatus.ERROR,
            duration_ms=round(duration_ms, 2),
            error=str(exc),
        )
    finally:
        if writer is not None:
            writer.close()
            try:
                await  writer.wait_closed()
            except OSError:
                pass
