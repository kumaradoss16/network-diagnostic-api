import asyncio
import logging
import platform
import re
import subprocess
import time

from ..schemas.responses import PingResult
from ..schemas.common import DiagnosticStatus
from ..utils.validators import resolve_to_ip

logger = logging.getLogger(__name__)

# Linux/macOS:
# time=12.3 ms
# time<1 ms
_UNIX_RTT_RE = re.compile(
    r"time[=<]\s*([\d.]+)\s*ms",
    re.IGNORECASE,
)

# Windows:
# time=12ms
# time<1ms
# time=12 ms
_WINDOWS_RTT_RE = re.compile(
    r"time[=<]\s*(\d+(?:\.\d+)?)\s*ms",
    re.IGNORECASE,
)


def build_ping_command(
    host: str,
    count: int,
    timeout: float,
) -> list[str]:

    system = platform.system().lower()

    if system == "windows":
        return [
            "ping",
            "-n",
            str(count),
            "-w",
            str(int(timeout * 1000)),
            host,
        ]

    return [
        "ping",
        "-c",
        str(count),
        "-W",
        str(max(1, int(timeout))),
        host,
    ]


def parse_rtts(output: str) -> list[float]:
    if platform.system().lower() == "windows":
        matches = _WINDOWS_RTT_RE.findall(output)
    else:
        matches = _UNIX_RTT_RE.findall(output)

    return [float(match) for match in matches]


async def _resolve(host: str) -> str | None:
    loop = asyncio.get_running_loop()

    return await loop.run_in_executor(
        None,
        resolve_to_ip,
        host,
    )


class PingExecutionError(Exception):
    """Raised when the system ping command cannot be executed."""

    pass


def _run_ping_sync(
    command: list[str],
    timeout: float,
) -> str:
    """
    Execute the operating-system ping command synchronously.

    This function runs inside a worker thread so that the
    FastAPI/asyncio event loop is not blocked.
    """

    overall_timeout = timeout * len(command) + 5

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            errors="ignore",
            timeout=overall_timeout,
            check=False,
        )

        return result.stdout + result.stderr

    except subprocess.TimeoutExpired as exc:
        raise PingExecutionError(
            "Ping command timed out."
        ) from exc

    except FileNotFoundError as exc:
        raise PingExecutionError(
            "The 'ping' utility is not available on this server."
        ) from exc

    except OSError as exc:
        raise PingExecutionError(
            f"Unable to execute ping command: {exc}"
        ) from exc


async def _execute_ping(
    host: str,
    count: int,
    timeout: float,
) -> list[float]:

    command = build_ping_command(
        host,
        count,
        timeout,
    )

    try:
        output = await asyncio.to_thread(
            _run_ping_sync,
            command,
            timeout,
        )

        return parse_rtts(output)

    except PingExecutionError:
        raise

    except Exception as exc:
        raise PingExecutionError(
            f"Unexpected ping execution error: {exc}"
        ) from exc


async def ping_host(
    host: str,
    count: int = 4,
    timeout: float = 2.0,
) -> PingResult:

    start = time.perf_counter()

    resolved_ip = await _resolve(host)

    try:
        rtts = await _execute_ping(
            host,
            count,
            timeout,
        )

    except PingExecutionError as exc:

        duration_ms = (
            time.perf_counter() - start
        ) * 1000

        logger.warning(
            "Ping execution failed for %s: %s",
            host,
            exc,
        )

        return PingResult(
            target=host,
            resolved_ip=resolved_ip,
            packets_sent=count,
            packets_received=0,
            packet_loss_percent=100.0,
            status=DiagnosticStatus.ERROR,
            duration_ms=round(duration_ms, 2),
            error=str(exc),
        )

    duration_ms = (
        time.perf_counter() - start
    ) * 1000

    if not rtts:

        logger.info(
            "Ping to %s produced no successful replies",
            host,
        )

        return PingResult(
            target=host,
            resolved_ip=resolved_ip,
            packets_sent=count,
            packets_received=0,
            packet_loss_percent=100.0,
            status=DiagnosticStatus.ERROR,
            duration_ms=round(duration_ms, 2),
            error=(
                "Host did not respond to any ping packets "
                "(unreachable, blocking ICMP or invalid host)."
            ),
        )

    packet_loss = round(
        (1 - len(rtts) / count) * 100,
        2,
    )

    return PingResult(
        target=host,
        resolved_ip=resolved_ip,
        packets_sent=count,
        packets_received=len(rtts),
        packet_loss_percent=packet_loss,
        min_rtt_ms=round(min(rtts), 2),
        avg_rtt_ms=round(sum(rtts) / len(rtts), 2),
        max_rtt_ms=round(max(rtts), 2),
        status=DiagnosticStatus.SUCCESS,
        duration_ms=round(duration_ms, 2),
    )
