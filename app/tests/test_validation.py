"""
Validation tests: confirm malformed input is rejected with 422 and the
consistent error envelope, before it ever reaches a service function.
"""


def test_ping_rejects_invalid_host(client):
    response = client.post("/api/v1/diagnostics/ping", json={"host": "not a valid host!!"})
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_ping_rejects_count_out_of_range(client):
    response = client.post("/api/v1/diagnostics/ping", json={"host": "example.com", "count": 50})
    assert response.status_code == 422


def test_port_check_rejects_invalid_port(client):
    response = client.post(
        "/api/v1/diagnostics/port", json={"host": "example.com", "port": 70000}
    )
    assert response.status_code == 422


def test_port_check_rejects_missing_fields(client):
    response = client.post("/api/v1/diagnostics/port", json={"host": "example.com"})
    assert response.status_code == 422


def test_http_check_rejects_invalid_url(client):
    response = client.post("/api/v1/diagnostics/http", json={"url": "not-a-url"})
    assert response.status_code == 422


def test_dns_rejects_empty_hostname(client):
    response = client.post("/api/v1/diagnostics/dns", json={"hostname": ""})
    assert response.status_code == 422


def test_latency_rejects_count_below_minimum(client):
    response = client.post(
        "/api/v1/diagnostics/latency", json={"host": "example.com", "count": 1}
    )
    assert response.status_code == 422
