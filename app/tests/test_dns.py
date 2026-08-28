"""
DNS tests mock socket.getaddrinfo so results are deterministic and the
suite doesn't depend on real DNS/network access.
"""

import socket

import pytest

from app.services import dns_service


@pytest.mark.asyncio
async def test_resolve_dns_success(monkeypatch):
    def fake_getaddrinfo(hostname, port):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
            (socket.AF_INET, socket.SOCK_DGRAM, 17, "", ("93.184.216.34", 0)),  # duplicate IP, different socktype
        ]

    monkeypatch.setattr(dns_service.socket, "getaddrinfo", fake_getaddrinfo)

    result = await dns_service.resolve_dns("example.com")

    assert result.status == "success"
    assert result.hostname == "example.com"
    assert result.ip_addresses == ["93.184.216.34"]  # deduplicated
    assert result.error is None


@pytest.mark.asyncio
async def test_resolve_dns_failure(monkeypatch):
    def fake_getaddrinfo(hostname, port):
        raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")

    monkeypatch.setattr(dns_service.socket, "getaddrinfo", fake_getaddrinfo)

    result = await dns_service.resolve_dns("this-domain-does-not-exist.invalid")

    assert result.status == "error"
    assert result.ip_addresses == []
    assert result.error is not None


def test_dns_endpoint_success(client, monkeypatch):
    async def fake_resolve_dns(hostname):
        from app.schemas.responses import DNSResult

        return DNSResult(
            hostname=hostname,
            ip_addresses=["93.184.216.34"],
            resolution_time_ms=5.0,
            status="success",
            duration_ms=5.0,
        )

    monkeypatch.setattr("app.api.v1.diagnostics.resolve_dns", fake_resolve_dns)

    response = client.post("/api/v1/diagnostics/dns", json={"hostname": "example.com"})

    assert response.status_code == 200
    body = response.json()
    assert body["hostname"] == "example.com"
    assert body["ip_addresses"] == ["93.184.216.34"]
    assert body["status"] == "success"
