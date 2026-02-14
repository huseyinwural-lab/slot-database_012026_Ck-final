import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


def _run_alembic(cmd: list[str], *, env: dict, cwd: str, timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)


def test_runtime_alembic_upgrade_head_on_fresh_sqlite():
    """URL-less determinism proof: fresh sqlite DB must migrate to head."""

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "smoke.db"
        # Pre-create empty file to ensure path exists.
        db_path.touch()

        # Alembic uses env.py which imports config via PYTHONPATH.
        env = {**os.environ}
        env["PYTHONPATH"] = "/app/backend"
        env["ENV"] = "local"
        env["CI_STRICT"] = "0"

        env["DATABASE_URL"] = f"sqlite+aiosqlite:////{db_path}"
        # Deterministic sync DSN for Alembic.
        env["SYNC_DATABASE_URL"] = f"sqlite:////{db_path}"

        cmd_upgrade = [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"]
        res = _run_alembic(cmd_upgrade, env=env, cwd="/app/backend", timeout=60)

        if res.returncode != 0:
            # Extra diagnosis (only on failure)
            diag = []
            try:
                heads = _run_alembic(
                    [sys.executable, "-m", "alembic", "-c", "alembic.ini", "heads"],
                    env=env,
                    cwd="/app/backend",
                    timeout=30,
                )
                diag.append("\n[alembic heads]\n" + (heads.stdout or "") + (heads.stderr or ""))
            except Exception as exc:  # pragma: no cover
                diag.append(f"\n[alembic heads FAILED] {exc}")

            try:
                current = _run_alembic(
                    [sys.executable, "-m", "alembic", "-c", "alembic.ini", "current"],
                    env=env,
                    cwd="/app/backend",
                    timeout=30,
                )
                diag.append("\n[alembic current]\n" + (current.stdout or "") + (current.stderr or ""))
            except Exception as exc:  # pragma: no cover
                diag.append(f"\n[alembic current FAILED] {exc}")

            raise AssertionError(
                "alembic upgrade head failed on fresh sqlite\n"
                f"exit={res.returncode}\n"
                f"STDOUT:\n{res.stdout}\n"
                f"STDERR:\n{res.stderr}\n"
                + "\n".join(diag)
            )

        # Validate alembic_version exists and has a non-empty version_num
        con = sqlite3.connect(str(db_path))
        try:
            cur = con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version' LIMIT 1"
            )
            assert cur.fetchone() is not None, "alembic_version table missing"

            cur = con.execute("SELECT version_num FROM alembic_version LIMIT 1")
            row = cur.fetchone()
            assert row is not None and row[0], "alembic_version.version_num is empty"
        finally:
            con.close()
