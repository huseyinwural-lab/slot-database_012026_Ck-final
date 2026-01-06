from __future__ import annotations

import csv
import io
from typing import Iterable, List, Dict, Any


def dicts_to_csv_bytes(rows: List[Dict[str, Any]], *, fieldnames: List[str]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    return buf.getvalue().encode("utf-8")
