from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_streamlit_app_starts_and_health_endpoint_is_ready():
    port = _free_port()
    env = os.environ.copy()
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.headless=true",
            f"--server.port={port}",
            "--server.address=127.0.0.1",
        ],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    try:
        deadline = time.monotonic() + 20
        health_url = f"http://127.0.0.1:{port}/_stcore/health"

        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise AssertionError(
                    f"Streamlit exited before becoming healthy with code {process.returncode}."
                )
            try:
                with urlopen(health_url, timeout=1) as response:
                    body = response.read().decode("utf-8", errors="replace")
                assert response.status == 200
                assert '"status": "ok"' in body or '"status":"ok"' in body
                return
            except (URLError, OSError, AssertionError):
                time.sleep(0.25)

        raise AssertionError("Streamlit did not become healthy within 20 seconds.")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
