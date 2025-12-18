from __future__ import annotations

import os
from pathlib import Path


def _read_repo_version_file() -> str | None:
    """Best-effort read of repo-root VERSION file.

    Safe: contains only semantic version string.
    """

    try:
        repo_root = Path(__file__).resolve().parents[3]  # /app
        version_path = repo_root / "VERSION"
        if not version_path.exists():
            return None
        raw = version_path.read_text(encoding="utf-8").strip()
        return raw or None
    except Exception:
        return None


def get_build_info(service: str) -> dict:
    """Return safe build metadata.

    IMPORTANT: Do not add env/hostname/config secrets here.

    Behavior:
    - Prefer build-time env vars (APP_VERSION/GIT_SHA/BUILD_TIME)
    - In dev/preview where env vars may not be set, fall back to repo VERSION file
    """

    env_version = os.environ.get("APP_VERSION", "unknown")
    version = env_version
    if (not env_version) or env_version == "unknown":
        version = _read_repo_version_file() or "unknown"

    return {
        "service": service,
        "version": version,
        "git_sha": os.environ.get("GIT_SHA", "unknown"),
        "build_time": os.environ.get("BUILD_TIME", "unknown"),
    }
