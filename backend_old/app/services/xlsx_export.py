from __future__ import annotations

import io
from typing import Any, Dict, List

from openpyxl import Workbook


def dicts_to_xlsx_bytes(rows: List[Dict[str, Any]], *, columns: List[str], sheet_name: str = "Players") -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    # header
    ws.append(columns)

    for r in rows:
        ws.append([r.get(c, "") for c in columns])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
