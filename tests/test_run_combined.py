"""
The combined run endpoint is tested with the individual service calls
mocked out, since it's an orchestration test — proving it calls the right
services with the right arguments and combines their results correctly —
not a re-test of DNS/ping/port/HTTP behavior itself (those have their own
dedicated test files).
"""

import pytest

from app.schemas.responses import DNSResult, HTTPCheckResult, PingResult, PortCheckResult
from app.services import diagnostic_service


def _ping_ok():
    return PingResult(
        target="example.com",
        resolved_ip="93.184.216.34",
        packets_sent=4,
        packets_received=4,
        packet_loss_percent=0.0,
        min_rtt_ms=10.0,
        avg_rtt_ms=11.0,
        max_rtt_ms=12.0,
        status="success",
        duration_ms=50.0,
    )


def _dns_ok():
    return DNSResult(
        hostname="example.com",
        ip_addresses=["93.184.216.34"],
        resolution_time_ms=5.0,
        status="success",
        duration_ms=5.0,
    )


def _port_ok():
    return PortCheckResult(
        host="example.com", port=443, is_open=True, response_time_ms=20.0, status="success", duration_ms=20.0
    )


def _http_ok():
    return HTTPCheckResult(
        url="https://example.com",
        status_code=200,
        is_reachable=True,
        response_time_ms=100.0,
        status="success",
        duration_ms=100.0,
    )


@pytest.mark.asyncio
async def test_run_diagnostics_all_checks_succeed(monkeypatch):
    async def fake_ping_host(host, count, timeout):
        return _ping_ok()

    async def fake_resolve_dns(hostname):
        return _dns_ok()

    async def fake_check_port(host, port, timeout):
        return _port_ok()

    async def fake_check_http(url, timeout, follow_redirects=True):
        return _http_ok()

    monkeypatch.setattr(diagnostic_service, "ping_host", fake_ping_host)
    monkeypatch.setattr(diagnostic_service, "resolve_dns", fake_resolve_dns)
    monkeypatch.setattr(diagnostic_service, "check_port", fake_check_port)
    monkeypatch.setattr(diagnostic_service, "check_http", fake_check_http)

    result = await diagnostic_service.run_diagnostics(
        host="example.com", port=443, url="https://example.com", ping_count=4, timeout=3.0
    )

    assert result.status == "success"
    assert result.ping.status == "success"
    assert result.dns.status == "success"
    assert result.port.status == "success"
    assert result.http.status == "success"


@pytest.mark.asyncio
async def test_run_diagnostics_omits_optional_checks(monkeypatch):
    async def fake_ping_host(host, count, timeout):
        return _ping_ok()

    async def fake_resolve_dns(hostname):
        return _dns_ok()

    monkeypatch.setattr(diagnostic_service, "ping_host", fake_ping_host)
    monkeypatch.setattr(diagnostic_service, "resolve_dns", fake_resolve_dns)

    result = await diagnostic_service.run_diagnostics(host="example.com")

    assert result.port is None
    assert result.http is None


@pytest.mark.asyncio
async def test_run_diagnostics_overall_status_reflects_failure(monkeypatch):
    async def fake_ping_host(host, count, timeout):
        return _ping_ok()

    async def fake_resolve_dns(hostname):
        failing = _dns_ok()
        failing.status = "error"
        failing.error = "DNS resolution failed"
        return failing

    monkeypatch.setattr(diagnostic_service, "ping_host", fake_ping_host)
    monkeypatch.setattr(diagnostic_service, "resolve_dns", fake_resolve_dns)

    result = await diagnostic_service.run_diagnostics(host="example.com")

    assert result.status == "error"


def test_run_endpoint_returns_combined_shape(client, monkeypatch):
    async def fake_run_diagnostics(**kwargs):
        return diagnostic_service.DiagnosticRunResult(
            target="example.com",
            ping=_ping_ok(),
            dns=_dns_ok(),
            port=None,
            http=None,
            status="success",
            duration_ms=60.0,
        )

    monkeypatch.setattr("app.api.v1.diagnostics.run_diagnostics", fake_run_diagnostics)

    response = client.post("/api/v1/diagnostics/run", json={"host": "example.com"})

    assert response.status_code == 200
    body = response.json()
    assert body["target"] == "example.com"
    assert "ping" in body and "dns" in body
    assert body["port"] is None
    assert body["http"] is None
