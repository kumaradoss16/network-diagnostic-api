import pytest

from app.services import latency_service


def test_calculate_jitter_typical_samples():
    jitter = latency_service._calculate_jitter([10.0, 12.0, 9.0, 11.0])
    # diffs: |12-10|=2, |9-12|=3, |11-9|=2 -> mean = 2.33
    assert jitter == pytest.approx(2.33, abs=0.01)


def test_calculate_jitter_single_sample_is_none():
    assert latency_service._calculate_jitter([10.0]) is None


def test_calculate_jitter_empty_is_none():
    assert latency_service._calculate_jitter([]) is None


@pytest.mark.asyncio
async def test_measure_latency_success(monkeypatch):
    async def fake_execute_ping(host, count, timeout):
        return [10.0, 11.0, 9.5, 10.5, 10.0]

    monkeypatch.setattr(latency_service, "_execute_ping", fake_execute_ping)

    result = await latency_service.measure_latency("example.com", count=5, timeout=2.0)

    assert result.status == "success"
    assert result.packets_received == 5
    assert result.packet_loss_percent == 0.0
    assert result.min_ms == 9.5
    assert result.max_ms == 11.0
    assert result.jitter_ms is not None


@pytest.mark.asyncio
async def test_measure_latency_no_samples(monkeypatch):
    async def fake_execute_ping(host, count, timeout):
        return []

    monkeypatch.setattr(latency_service, "_execute_ping", fake_execute_ping)

    result = await latency_service.measure_latency("10.255.255.1", count=5, timeout=2.0)

    assert result.status == "error"
    assert result.packets_received == 0
    assert result.error is not None
