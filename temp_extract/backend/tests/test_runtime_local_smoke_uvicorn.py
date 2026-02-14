import os
import subprocess
import sys
import time
from urllib.request import urlopen


def _http_get_status(url: str) -> int:
    with urlopen(url, timeout=2) as resp:
        return resp.status


def _start_uvicorn(env_overrides: dict) -> subprocess.Popen:
    env = {**os.environ, **env_overrides}
    env.pop("CI_STRICT", None)
    env.pop("DATABASE_URL", None)
    env.pop("REDIS_URL", None)
    env["PYTHONPATH"] = "/app/backend"

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "server:app",
        "--host",
        "0.0.0.0",
        "--port",
        "18001",
    ]

    return subprocess.Popen(
        cmd,
        cwd="/app/backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )


def test_runtime_local_smoke_health_and_ready():
    proc = _start_uvicorn({"ENV": "local"})

    try:
        deadline = time.time() + 15
        health_ok = False
        ready_ok = False

        while time.time() < deadline:
            # If server died early, fail with logs
            if proc.poll() is not None:
                out, err = proc.communicate(timeout=2)
                raise AssertionError(
                    f"uvicorn exited unexpectedly with code {proc.returncode}.\nSTDOUT:\n{out}\nSTDERR:\n{err}"
                )

            try:
                if not health_ok:
                    health_ok = _http_get_status("http://127.0.0.1:18001/api/health") == 200
                if health_ok and not ready_ok:
                    ready_ok = _http_get_status("http://127.0.0.1:18001/api/ready") == 200

                if health_ok and ready_ok:
                    break
            except Exception:
                # Not ready yet
                pass

            time.sleep(0.5)

        assert health_ok, "Expected /api/health to return 200 within timeout"
        assert ready_ok, "Expected /api/ready to return 200 within timeout"

    finally:
        # Always cleanup
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)
