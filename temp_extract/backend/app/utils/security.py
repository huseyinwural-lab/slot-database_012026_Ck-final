from __future__ import annotations

import hashlib


def sha256_surrogate(value: str) -> str:
    """Return a stable, PII-minimized surrogate identifier.

    - Normalizes by trim + lower
    - Returns hex digest
    """

    normalized = (value or "").strip().lower().encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()
