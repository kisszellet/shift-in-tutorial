"""CI gate for SLI 1 (docs/slis.md): redirect latency.

p95 time to answer `GET /{code}` must be under 50 ms. Runs against a real
uvicorn server over a socket, not the in-process TestClient.
"""

import math
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]

SLO_P95_MS = 50  # docs/slis.md, SLI 1: "p95 server time to answer GET /{code} < 50 ms"
SAMPLES = 200
WARMUP = 20


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def base_url():
    port = free_port()
    server = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "snip.main:app",
            "--app-dir", str(ROOT / "src"),
            "--host", "127.0.0.1", "--port", str(port),
            "--log-level", "warning",
        ],
        cwd=ROOT,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 15
        while True:
            if server.poll() is not None:
                pytest.fail(f"uvicorn exited early with code {server.returncode}")
            try:
                httpx.get(f"{url}/api/links", timeout=1)
                break
            except httpx.TransportError:
                if time.monotonic() > deadline:
                    pytest.fail("uvicorn did not start within 15 s")
                time.sleep(0.1)
        yield url
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


def p95(samples_ms: list[float]) -> float:
    """Nearest-rank 95th percentile."""
    ordered = sorted(samples_ms)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


def test_redirect_p95_latency_is_under_the_slo(base_url, capsys):
    with httpx.Client(base_url=base_url, follow_redirects=False) as client:
        code = client.post("/api/links", json={"url": "https://example.com"}).json()["code"]

        for _ in range(WARMUP):
            client.get(f"/{code}")

        samples_ms = []
        for _ in range(SAMPLES):
            start = time.perf_counter()
            response = client.get(f"/{code}")
            samples_ms.append((time.perf_counter() - start) * 1000)
            assert response.status_code == 307

    measured = p95(samples_ms)
    with capsys.disabled():
        print(
            f"\nSLI 1 redirect latency: p95 = {measured:.2f} ms "
            f"(SLO < {SLO_P95_MS} ms, margin {SLO_P95_MS - measured:.2f} ms; "
            f"n={SAMPLES}, min={min(samples_ms):.2f}, max={max(samples_ms):.2f} ms)"
        )

    assert measured < SLO_P95_MS
