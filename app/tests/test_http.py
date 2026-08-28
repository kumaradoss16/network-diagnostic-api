"""
HTTP-check tests run a real local HTTP server (see conftest.py) rather
than mocking httpx internals, so the request/response cycle is exercised
end to end without depending on external network access.
"""

import pytest

from app.services.http_service import check_http


@pytest.mark.asyncio
async def test_check_http_reachable(local_http_server):
    result = await check_http(local_http_server, timeout=3.0)

    assert result.status == "success"
    assert result.is_reachable is True
    assert result.status_code == 200
    assert result.response_time_ms is not None


@pytest.mark.asyncio
async def test_check_http_connection_refused():
    # Port 1 is a reserved, near-universally-unbound port, so the
    # connection should be refused quickly and deterministically.
    result = await check_http("http://127.0.0.1:1", timeout=2.0)

    assert result.status == "error"
    assert result.is_reachable is False
    assert result.error is not None


def test_http_endpoint_success(client, monkeypatch, local_http_server):
    response = client.post(
        "/api/v1/diagnostics/http", json={"url": local_http_server, "timeout": 3.0}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_reachable"] is True
    assert body["status_code"] == 200
