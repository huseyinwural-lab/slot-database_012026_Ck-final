from __future__ import annotations

import os


def get_build_info(service: str) -> dict:
    """Return safe build metadata.

    IMPORTANT: Do not add env/hostname/config secrets here.
    """

    return {
        "service": service,
        "version": os.environ.get("APP_VERSION", "unknown"),
        "git_sha": os.environ.get("GIT_SHA", "unknown"),
        "build_time": os.environ.get("BUILD_TIME", "unknown"),
    }
