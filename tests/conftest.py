import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def open_tcp_port():
    """
    Bind and listen on an OS-assigned local port and yield its number.

    A TCP handshake completes as soon as the OS is listening on the port —
    no application-level accept() loop is required — so this is enough to
    give the port-check service a real, deterministic "open port" to test
    against without hitting the network.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    port = sock.getsockname()[1]
    yield port
    sock.close()


@pytest.fixture
def closed_tcp_port():
    """
    Bind to an OS-assigned port, then close it immediately, so the port
    number is very likely free and will refuse connections (ECONNREFUSED)
    when the port-check service tries it.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class _EchoHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (stdlib naming convention)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):  # noqa: A002 - suppress request logging in test output
        pass


@pytest.fixture
def local_http_server():
    """Run a minimal real HTTP server on localhost for HTTP-check tests."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _EchoHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    yield f"http://{host}:{port}"
    server.shutdown()
    thread.join(timeout=2)
