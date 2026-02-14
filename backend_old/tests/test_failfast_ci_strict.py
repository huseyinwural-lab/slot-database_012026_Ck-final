import os
import subprocess
import sys


BACKEND_DIR = "/app/backend"


def _run_import_server(env: dict) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    merged.update(env)
    # Ensure clean pythonpath
    cmd = [sys.executable, "-c", "import sys; sys.path.insert(0, '/app/backend'); import server"]
    return subprocess.run(cmd, capture_output=True, text=True, env=merged)


def test_ci_strict_database_url_unset_fails():
    res = _run_import_server({"CI_STRICT": "1", "ENV": "dev", "DATABASE_URL": ""})
    assert res.returncode != 0
    assert "DATABASE_URL must be set" in (res.stderr + res.stdout)


def test_ci_strict_sqlite_database_url_fails():
    res = _run_import_server({
        "CI_STRICT": "1",
        "ENV": "dev",
        "DATABASE_URL": "sqlite+aiosqlite:////tmp/test_ci_strict.db",
    })
    assert res.returncode != 0
    assert "SQLite DATABASE_URL is not allowed" in (res.stderr + res.stdout)


def test_local_database_url_unset_allows_sqlite_fallback():
    # Local/dev: sqlite fallback is allowed.
    env = {"CI_STRICT": "0", "ENV": "local"}
    env.pop("DATABASE_URL", None)
    res = _run_import_server(env)
    assert res.returncode == 0, (res.stderr + res.stdout)
