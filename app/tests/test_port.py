"""
Port-check tests use real local TCP sockets (see conftest.py fixtures)
rather than mocking asyncio internals, so the actual open_connection
behavior is exercised end to end.
"""

import pytest

from app.services.port_service import check_port


@pytest.mark.asyncio
async def test_check_port_open(open_tcp_port):
    result = await check_port("127.0.0.1", open_tcp_port, timeout=2.0)

    assert result.status == "success"
    assert result.is_open is True
    assert result.response_time_ms is not None
    assert result.error is None


@pytest.mark.asyncio
async def test_check_port_closed(closed_tcp_port):
    result = await check_port("127.0.0.1", closed_tcp_port, timeout=2.0)

    assert result.status == "error"
    assert result.is_open is False
    assert result.error is not None


def test_port_endpoint_returns_200_even_when_closed(client, closed_tcp_port):
    """
    A closed port is a valid diagnostic answer, not a server error — the
    endpoint should return HTTP 200 with status='error' in the body, not
    a 4xx/5xx.
    """
    response = client.post(
        "/api/v1/diagnostics/port",
        json={"host": "127.0.0.1", "port": closed_tcp_port, "timeout": 1.0},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_open"] is False
    assert body["status"] == "error"
