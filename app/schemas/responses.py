from pydantic import Field
from .common import ResultBase

# Model represents the result of a ping diagnostic.
class PingResult(ResultBase):
    target: str
    resolved_ip: str | None = None
    packets_sent: int
    packets_received: int
    packet_loss_percent: float
    min_rtt_ms: float | None = None
    avg_rtt_ms: float | None = None
    max_rtt_ms: float | None = None

# Model represents a DNS lookup result
class DNSResult(ResultBase):
    hostname: str
    ip_addresses: list[str] = Field(default_factory=list)
    resolution_time_ms: float | None = None

# Model represents the result of checking whether a TCP port is accepting connections
class PortCheckResult(ResultBase):
    host: str
    port: int
    is_open: bool
    response_time_ms: float | None = None

# Model represents an HTTP or HTTPS check
class HTTPCheckResult(ResultBase):
    url: str
    status_code: int | None = None
    is_reachable: bool
    response_time_ms: float | None = None
    final_url: str | None = Field(default=None, description="URL after following redirects, if different.")

# Model represents repeated latency measurements.
class LatencyResult(ResultBase):
    target: str
    samples_ms: list[float] = Field(default_factory=list)
    packets_sent: int
    packets_received: int
    packet_loss_percent: float
    min_ms: float | None = None
    avg_ms: float | None = None
    max_ms: float | None = None
    jitter_ms: float | None = None

# Model represents a combined diagnostic run
class DiagnosticRunResult(ResultBase):
    target: str
    ping: PingResult
    dns: DNSResult
    port: PortCheckResult | None = None
    http: HTTPCheckResult | None = None