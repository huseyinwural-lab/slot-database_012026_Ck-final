import os
import subprocess
import sys


def _run_alembic(args: list[str], *, timeout: int = 30) -> subprocess.CompletedProcess:
    env = {**os.environ}
    env["PYTHONPATH"] = "/app/backend"
    return subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", *args],
        cwd="/app/backend",
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_alembic_heads_single_head_guard():
    # Allow explicit bypass only when intentionally working with multi-head.
    if (os.getenv("ALLOW_MULTI_HEAD") or "").strip().lower() in {"1", "true", "yes"}:
        return

    res = _run_alembic(["heads", "--verbose"], timeout=30)
    assert res.returncode == 0, f"alembic heads failed\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"

    # Heuristic: each head prints a 'Revision ID:' line in verbose output.
    head_count = sum(1 for line in (res.stdout or "").splitlines() if line.strip().startswith("Revision ID:"))

    assert head_count == 1, (
        "Expected exactly 1 Alembic head (single linear migration chain).\n"
        f"Found heads={head_count}.\n\n"
        "If this is intentional, set ALLOW_MULTI_HEAD=1 for that run.\n\n"
        f"alembic heads --verbose output:\n{res.stdout}\n{res.stderr}"
    )


def test_alembic_history_base_to_heads_non_empty():
    res = _run_alembic(["history", "--verbose", "-r", "base:heads"], timeout=30)
    assert res.returncode == 0, (
        "alembic history base:heads failed\n"
        f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    )

    # Must contain at least one revision line
    assert "Revision ID:" in (res.stdout or ""), (
        "alembic history base:heads returned empty or unexpected output\n"
        f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    )
