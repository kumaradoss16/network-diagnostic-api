"""
Ping tests split into two kinds:

1. Pure-function tests for command building and output parsing — these
   don't touch the network or a subprocess at all, so they're fast and
   fully deterministic.
2. ping_host() tests with asyncio.create_subprocess_exec mocked out, since
   actually invoking ICMP ping requires a `ping` binary and often elevated
   privileges, neither of which should be a CI/test requirement.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import ping_service

LINUX_PING_OUTPUT = """PING example.com (93.184.216.34) 56(84) bytes of data.
64 bytes from 93.184.216.34: icmp_seq=1 ttl=56 time=11.2 ms
64 bytes from 93.184.216.34: icmp_seq=2 ttl=56 time=10.8 ms
64 bytes from 93.184.216.34: icmp_seq=3 ttl=56 time=12.1 ms

--- example.com ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2003ms
rtt min/avg/max/mdev = 10.800/11.366/12.100/0.545 ms
"""

WINDOWS_PING_OUTPUT = """
Pinging example.com [93.184.216.34] with 32 bytes of data:
Reply from 93.184.216.34: bytes=32 time=11ms TTL=56
Reply from 93.184.216.34: bytes=32 time=10ms TTL=56

Ping statistics for 93.184.216.34:
    Packets: Sent = 2, Received = 2, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 10ms, Maximum = 11ms, Average = 10ms
"""

UNREACHABLE_OUTPUT = """PING 10.255.255.1 (10.255.255.1) 56(84) bytes of data.

--- 10.255.255.1 ping statistics ---
3 packets transmitted, 0 received, 100% packet loss, time 2045ms
"""


def test_build_ping_command_linux(monkeypatch):
    monkeypatch.setattr(ping_service.platform, "system", lambda: "Linux")
    command = ping_service.build_ping_command("example.com", count=4, timeout=2.0)
    assert command == ["ping", "-c", "4", "-W", "2", "example.com"]


def test_build_ping_command_windows(monkeypatch):
    monkeypatch.setattr(ping_service.platform, "system", lambda: "Windows")
    command = ping_service.build_ping_command("example.com", count=4, timeout=2.0)
    assert command == ["ping", "-n", "4", "-w", "2000", "example.com"]


def test_parse_rtts_linux_output(monkeypatch):
    monkeypatch.setattr(ping_service.platform, "system", lambda: "Linux")
    rtts = ping_service.parse_rtts(LINUX_PING_OUTPUT)
    assert rtts == [11.2, 10.8, 12.1]


def test_parse_rtts_windows_output(monkeypatch):
    monkeypatch.setattr(ping_service.platform, "system", lambda: "Windows")
    rtts = ping_service.parse_rtts(WINDOWS_PING_OUTPUT)
    assert rtts == [11.0, 10.0]


def test_parse_rtts_no_replies(monkeypatch):
    monkeypatch.setattr(ping_service.platform, "system", lambda: "Linux")
    rtts = ping_service.parse_rtts(UNREACHABLE_OUTPUT)
    assert rtts == []


@pytest.mark.asyncio
async def test_ping_host_success(monkeypatch):
    fake_process = SimpleNamespace(
        communicate=AsyncMock(return_value=(LINUX_PING_OUTPUT.encode(), b""))
    )

    async def fake_create_subprocess_exec(*args, **kwargs):
        return fake_process

    monkeypatch.setattr(ping_service.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr(ping_service, "resolve_to_ip", lambda host: "93.184.216.34")
    monkeypatch.setattr(ping_service.platform, "system", lambda: "Linux")

    result = await ping_service.ping_host("example.com", count=3, timeout=2.0)

    assert result.status == "success"
    assert result.resolved_ip == "93.184.216.34"
    assert result.packets_received == 3
    assert result.packet_loss_percent == 0.0
    assert result.avg_rtt_ms == pytest.approx(11.37, abs=0.05)


@pytest.mark.asyncio
async def test_ping_host_unreachable(monkeypatch):
    fake_process = SimpleNamespace(
        communicate=AsyncMock(return_value=(UNREACHABLE_OUTPUT.encode(), b""))
    )

    async def fake_create_subprocess_exec(*args, **kwargs):
        return fake_process

    monkeypatch.setattr(ping_service.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr(ping_service, "resolve_to_ip", lambda host: None)
    monkeypatch.setattr(ping_service.platform, "system", lambda: "Linux")

    result = await ping_service.ping_host("10.255.255.1", count=3, timeout=2.0)

    assert result.status == "error"
    assert result.packets_received == 0
    assert result.packet_loss_percent == 100.0
    assert result.error is not None


@pytest.mark.asyncio
async def test_ping_host_missing_binary(monkeypatch):
    async def fake_create_subprocess_exec(*args, **kwargs):
        raise FileNotFoundError("ping: not found")

    monkeypatch.setattr(ping_service.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr(ping_service, "resolve_to_ip", lambda host: None)

    result = await ping_service.ping_host("example.com", count=2, timeout=2.0)

    assert result.status == "error"
    assert "not available" in result.error
