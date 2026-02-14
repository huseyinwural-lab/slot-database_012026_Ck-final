import os
import re
import subprocess
import sys


def _run_uvicorn(env_overrides: dict, *, timeout_seconds: int = 5) -> tuple[int, str]:
    env = {**os.environ, **env_overrides}
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

    proc = subprocess.Popen(
        cmd,
        cwd="/app/backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    try:
        out, err = proc.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate(timeout=2)
        raise AssertionError(
            f"uvicorn did not exit within {timeout_seconds}s (not fail-fast).\nSTDOUT:\n{out}\nSTDERR:\n{err}"
        )

    combined = (out or "") + "\n" + (err or "")
    return proc.returncode or 0, combined


def test_runtime_failfast_ci_strict_redis_url_unset_fails_when_required():
    # Redis is optional unless REDIS_REQUIRED=true.
    code, logs = _run_uvicorn(
        {
            "ENV": "dev",
            "CI_STRICT": "1",
            "DATABASE_URL": "postgresql+asyncpg://user:pass@127.0.0.1:1/db",
            "REDIS_REQUIRED": "true",
            "REDIS_URL": "",
        },
        timeout_seconds=5,
    )

    assert code != 0
    assert "Uvicorn running on" not in logs
    assert re.search(r"REDIS_URL", logs, re.IGNORECASE) is not None
