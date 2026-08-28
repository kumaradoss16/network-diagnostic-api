import logging
import time
from ..schemas.responses import LatencyResult
from ..services.ping_service import PingExecutionError, _execute_ping
from ..schemas.common import DiagnosticStatus

logger = logging.getLogger(__name__)

# Receives latency samples and returns the estimated jitter.
def _calculate_jitter(samples: list[float]) -> float | None:
    if len(samples) < 2:
        return None
    diffs = [abs(samples[i] - samples[i - 1]) for i in range(1, len(samples))]
    return round(sum(diffs) / len(diffs), 2)

async def measure_latency(host: str, count: int = 5, timeout: float = 2.0) -> LatencyResult:
    start = time.perf_counter()
    try:
        samples = await _execute_ping(host, count, timeout)
    except PingExecutionError as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.warning("Latency measurement failed for %s: %s", host, exc)
        return LatencyResult(
            target=host,
            samples_ms=[],
            packets_sent=count,
            packets_received=0,
            packet_loss_percent=100.0,
            status=DiagnosticStatus.ERROR,
            duration_ms=round(duration_ms, 2),
            error=str(exc),
        )

    duration_ms = (time.perf_counter() - start) * 1000
    # checks whether the list is empty
    if not samples:
        return LatencyResult(
            target=host,
            samples_ms=[],
            packets_sent=count,
            packets_received=0,
            packet_loss_percent=100.0,
            status=DiagnosticStatus.ERROR,
            duration_ms=round(duration_ms, 2),
            error="No latency samples were collected (host unreachable or blocking ICMP).",
        )

    packet_loss = round(1 - len(samples) / count * 100, 2)
    return LatencyResult(
        target=host,
        samples_ms=[round(s, 2) for s in samples],
        packets_sent=count,
        packets_received=len(samples),
        packet_loss_percent=packet_loss,
        min_ms=round(min(samples), 2),
        avg_ms=round(sum(samples) / len(samples), 2),
        max_ms=round(max(samples), 2),
        jitter_ms=_calculate_jitter(samples),
        status=DiagnosticStatus.SUCCESS,
        duration_ms=round(duration_ms, 2),
    )

