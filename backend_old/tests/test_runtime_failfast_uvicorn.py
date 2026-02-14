import os
import re
import subprocess
import sys


def _run_uvicorn(env_overrides: dict, *, timeout_seconds: int = 5) -> tuple[int, str]:
    env = {**os.environ, **env_overrides}
    # Ensure child can import backend modules (server.py, config.py, app/*)
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


def test_runtime_failfast_ci_strict_database_url_unset():
    code, logs = _run_uvicorn(
        {
            "ENV": "staging",
            "CI_STRICT": "1",
            "DATABASE_URL": "",
            "REDIS_URL": "",
        }
    )

    assert code != 0, f"Expected non-zero exit code. Logs:\n{logs}"

    # Must not reach 'listening' state
    assert "Uvicorn running on" not in logs

    # Do not bind to exact message; use contains/regex.
    assert (
        re.search(r"DATABASE_URL", logs, re.IGNORECASE) is not None
    ), f"Expected DATABASE_URL-related error in logs. Logs:\n{logs}"


def test_runtime_failfast_ci_strict_sqlite_database_url():
    code, logs = _run_uvicorn(
        {
            "ENV": "staging",
            "CI_STRICT": "1",
            "DATABASE_URL": "sqlite+aiosqlite:////tmp/test.db",
        }
    )

    assert code != 0, f"Expected non-zero exit code. Logs:\n{logs}"
    assert "Uvicorn running on" not in logs

    assert (
        re.search(r"sqlite", logs, re.IGNORECASE) is not None
        or re.search(r"not allowed", logs, re.IGNORECASE) is not None
    ), f"Expected SQLite-not-allowed error in logs. Logs:\n{logs}"
