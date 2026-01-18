import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict, Tuple
from urllib.parse import urlparse

import psutil


TARGET_ENV = "REQUESTS_TARGET"
ROOT_DIR = Path(__file__).resolve().parents[2]


def _looks_like_repo_root(repo_root: Path) -> bool:
    return (repo_root / "requests" / "__init__.py").exists()


def _select_repo_root() -> Path:
    override = os.environ.get("RACB_REPO_ROOT")
    if override:
        p = Path(override).resolve()
        if _looks_like_repo_root(p):
            return p

    target = os.environ.get(TARGET_ENV, "generated").lower()
    if target == "reference":
        return (ROOT_DIR / "repositories" / "requests").resolve()

    return (ROOT_DIR / "generation" / "Requests").resolve()


REPO_ROOT = _select_repo_root()
repo_str = str(REPO_ROOT)
if repo_str not in sys.path:
    sys.path.insert(0, repo_str)

import requests  # noqa: E402


def _new_session() -> requests.Session:
    s = requests.Session()
    s.trust_env = False
    return s


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/ping":
            body = b"pong"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()


def _start_server() -> Tuple[HTTPServer, str]:
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    host, port = httpd.server_address
    base_url = f"http://{host}:{port}"
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, base_url


def run_requests_resource_probe(iterations: int = 60) -> Dict[str, float]:
    httpd, base_url = _start_server()
    s = _new_session()
    process = psutil.Process(os.getpid())
    try:
        # Warmup
        for _ in range(10):
            r = s.get(base_url + "/ping", timeout=2.0)
            r.raise_for_status()

        mem_before = float(process.memory_info().rss) / (1024 * 1024)
        cpu_before = process.cpu_times()
        t0 = time.perf_counter()

        for _ in range(iterations):
            r = s.get(base_url + "/ping", timeout=2.0)
            r.raise_for_status()

        elapsed = time.perf_counter() - t0
        cpu_after = process.cpu_times()
        mem_after = float(process.memory_info().rss) / (1024 * 1024)

        cpu_used_s = float((cpu_after.user + cpu_after.system) - (cpu_before.user + cpu_before.system))
        cpu_percent = float((cpu_used_s / elapsed) * 100.0) if elapsed > 0 else 0.0

        return {
            "iterations": float(iterations),
            "elapsed_seconds": float(elapsed),
            "memory_mb_before": float(mem_before),
            "memory_mb_after": float(mem_after),
            "memory_mb_delta": float(mem_after - mem_before),
            "cpu_percent": float(cpu_percent),
        }
    finally:
        s.close()
        httpd.shutdown()
        httpd.server_close()


def test_requests_resource_usage_smoke() -> None:
    m = run_requests_resource_probe(iterations=40)
    assert m["iterations"] == 40.0
    assert m["elapsed_seconds"] >= 0.0
    assert m["memory_mb_before"] > 0.0
    assert m["memory_mb_after"] > 0.0
    assert m["cpu_percent"] >= 0.0
