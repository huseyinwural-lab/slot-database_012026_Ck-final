from __future__ import annotations

import json
import os
import zipfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from fastapi import UploadFile


MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_ITEMS = 10_000


@dataclass
class StoredUpload:
    path: str
    file_name: str
    file_type: str  # json|zip
    size_bytes: int


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


async def store_upload_file_to_tmp(upload: UploadFile, *, job_id: str) -> StoredUpload:
    base_dir = "/tmp/game-import"
    _ensure_dir(base_dir)

    filename = (upload.filename or "upload").strip() or "upload"
    content_type = (upload.content_type or "").lower()

    # Detect type by content-type/extension
    ext = os.path.splitext(filename)[1].lower()
    if "zip" in content_type or ext == ".zip":
        ftype = "zip"
        out_path = os.path.join(base_dir, f"{job_id}.zip")
    elif "json" in content_type or ext == ".json":
        ftype = "json"
        out_path = os.path.join(base_dir, f"{job_id}.json")
    else:
        # fallback: attempt to parse as json
        ftype = "json"
        out_path = os.path.join(base_dir, f"{job_id}.json")

    size = 0
    with open(out_path, "wb") as f:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                raise ValueError("UPLOAD_TOO_LARGE")
            f.write(chunk)

    return StoredUpload(path=out_path, file_name=filename, file_type=ftype, size_bytes=size)


def _select_zip_member(zf: zipfile.ZipFile) -> str:
    # Zip slip hardening: reject suspicious paths
    names = [n for n in zf.namelist() if not n.endswith("/")]
    safe = []
    for n in names:
        nn = n.replace("\\", "/")
        if nn.startswith("/") or "../" in nn or nn.startswith(".."):
            continue
        safe.append(n)

    if not safe:
        raise ValueError("ZIP_EMPTY")

    # Prefer games.json
    for n in safe:
        if n.lower().endswith("games.json"):
            return n

    # Else first json
    for n in safe:
        if n.lower().endswith(".json"):
            return n

    raise ValueError("ZIP_NO_JSON")


def extract_json_bytes(stored: StoredUpload) -> bytes:
    if stored.file_type == "json":
        with open(stored.path, "rb") as f:
            return f.read()

    if stored.file_type != "zip":
        raise ValueError("UNSUPPORTED_FILE")

    with zipfile.ZipFile(stored.path, "r") as zf:
        member = _select_zip_member(zf)
        data = zf.read(member)
        return data


def parse_items(json_bytes: bytes) -> List[Dict[str, Any]]:
    try:
        obj = json.loads(json_bytes.decode("utf-8"))
    except Exception as exc:
        raise ValueError("JSON_PARSE_ERROR") from exc

    if isinstance(obj, list):
        items = obj
    elif isinstance(obj, dict):
        # common schema: {items:[...]}
        items = obj.get("items")
        if items is None and "games" in obj and isinstance(obj.get("games"), list):
            items = obj.get("games")
    else:
        items = None

    if not isinstance(items, list):
        raise ValueError("JSON_SCHEMA_INVALID")

    if len(items) > MAX_ITEMS:
        raise ValueError("TOO_MANY_ITEMS")

    out: List[Dict[str, Any]] = []
    for it in items:
        if isinstance(it, dict):
            out.append(it)
        else:
            out.append({"value": it})
    return out


def normalize_item(raw: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[float], List[str]]:
    errors: List[str] = []

    provider_id = raw.get("provider_id") or raw.get("provider") or raw.get("provider_key")

    external_id = (
        raw.get("external_id")
        or raw.get("provider_game_id")
        or raw.get("id")
        or raw.get("game_id")
    )

    if not external_id or not str(external_id).strip():
        errors.append("MISSING_EXTERNAL_ID")
        external_id = None
    else:
        external_id = str(external_id).strip()

    name = raw.get("name") or raw.get("title")
    if name is not None:
        name = str(name)

    gtype = raw.get("type") or raw.get("category")
    if gtype is not None:
        gtype = str(gtype)

    rtp_val = raw.get("rtp")
    rtp: Optional[float] = None
    if rtp_val is not None:
        try:
            rtp = float(rtp_val)
        except Exception:
            errors.append("INVALID_RTP")

    return external_id, (str(provider_id).strip() if provider_id else None), name, gtype, rtp, errors
