from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging
import json
import zipfile
import io
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient

from config import settings
from app.models.core import Game
from app.models.game import GameConfigVersion, GameConfigVersionStatus, GameLog
from app.models.game_import import GameImportJob, GameImportItem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/game-import", tags=["game_import"])


def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]


async def _append_game_log(db, game_id: str, admin_id: str, action: str, details: Dict[str, Any]):
    log = GameLog(game_id=game_id, admin_id=admin_id, action=action, details=details)
    await db.game_logs.insert_one(log.model_dump())


async def _generate_new_version(db, game_id: str, admin_id: str, notes: Optional[str] = None) -> GameConfigVersion:
    latest = await db.game_config_versions.find({"game_id": game_id}, {"_id": 0}).sort("created_at", -1).limit(1).to_list(1)
    if latest:
        last_ver = latest[0].get("version", "1.0.0")
        parts = last_ver.split(".")
        try:
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
            patch += 1
        except Exception:
            major, minor, patch = 1, 0, 0
        new_version = f"{major}.{minor}.{patch}"
    else:
        new_version = "1.0.0"

    version = GameConfigVersion(
        game_id=game_id,
        version=new_version,
        created_by=admin_id,
        status=GameConfigVersionStatus.DRAFT,
        notes=notes,
    )
    await db.game_config_versions.insert_one(version.model_dump())
    await db.games.update_one({"id": game_id}, {"$set": {"current_config_version_id": version.id}})
    return version


def _validation_error(message: str, field: str, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "error_code": "GAME_IMPORT_VALIDATION_FAILED",
        "message": message,
        "details": {
            "field": field,
            "errors": errors or [],
            "warnings": warnings or [],
        },
    }


@router.post("/manual/upload")
async def manual_upload(
    request: Request,
    file: UploadFile = File(...),
    source_label: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
):
    """Handle manual game import via JSON or ZIP bundle."""
    db = get_db()
    admin_id = "current_admin"  # TODO: integrate real auth
    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    filename = file.filename or "upload.bin"
    content = await file.read()

    if filename.lower().endswith(".json"):
        try:
            payload = json.loads(content.decode("utf-8"))
        except Exception:
            err = _validation_error("JSON içeriği parse edilemedi.", "file")
            return JSONResponse(status_code=400, content=err)
    elif filename.lower().endswith(".zip"):
        try:
            zf = zipfile.ZipFile(io.BytesIO(content))
        except Exception:
            err = _validation_error("ZIP dosyası açılamadı.", "file")
            return JSONResponse(status_code=400, content=err)

        if "game.json" not in zf.namelist():
            err = _validation_error("ZIP içinde game.json bulunamadı.", "file")
            return JSONResponse(status_code=400, content=err)

        with zf.open("game.json") as gf:
            try:
                payload = json.loads(gf.read().decode("utf-8"))
            except Exception:
                err = _validation_error("game.json içeriği parse edilemedi.", "file")
                return JSONResponse(status_code=400, content=err)
    else:
        err = _validation_error("Sadece .json veya .zip dosyaları desteklenmektedir.", "file")
        return JSONResponse(status_code=400, content=err)

    # Extract minimal metadata
    game_id = payload.get("game_id")
    name = payload.get("name")
    category = payload.get("category")
    core_type = payload.get("core_type")
    rtp = payload.get("rtp")

    errors: List[str] = []
    warnings: List[str] = []

    if not game_id:
        errors.append("game_id is required")
    if not name:
        errors.append("name is required")
    if not category:
        errors.append("category is required")
    if not core_type:
        errors.append("core_type is required")

    valid_categories = {"slot", "live", "table", "crash", "dice"}
    if category and category not in valid_categories:
        errors.append(f"category must be one of {sorted(valid_categories)}")

    # RTP checks
    if rtp is None:
        warnings.append("rtp is not set; engine will need a default later")
    else:
        try:
            rtp_val = float(rtp)
            if rtp_val < 80 or rtp_val > 99.9:
                warnings.append("rtp is outside typical range (80-99.9)")
        except Exception:
            errors.append("rtp must be numeric if provided")

    config = payload.get("config") or {}

    if category == "slot":
        if "paytable" not in config:
            warnings.append("Slot game without paytable config")
        if "reels" not in config:
            warnings.append("Slot game without reels config")

    if category in {"crash", "dice"}:
        if "math" not in config:
            warnings.append("Math config missing for crash/dice game")

    # Duplicate check
    existing_game = await db.games.find_one({"provider_game_id": game_id})
    already_exists = bool(existing_game)
    if already_exists:
        errors.append("Game with this game_id / provider_game_id already exists")

    # Create import job
    job = GameImportJob(
        provider=None,
        source="manual",
        status="fetched" if not errors else "failed",
        created_by=admin_id,
        total_found=1,
        total_imported=0,
        total_errors=len(errors),
        total_warnings=len(warnings),
        logs=[
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "game_import_manual_uploaded",
                "request_id": request_id,
                "filename": filename,
                "errors": errors,
                "warnings": warnings,
            }
        ],
    )

    await db.game_import_jobs.insert_one(job.model_dump())

    item_status = "ready" if not errors and not already_exists else "error"

    item = GameImportItem(
        job_id=job.id,
        provider=None,
        provider_game_id=game_id or "unknown",
        name=name or "unknown",
        category=category or "unknown",
        rtp=rtp,
        status=item_status,
        errors=errors,
        warnings=warnings,
        already_exists=already_exists,
        raw_payload=payload,
    )

    await db.game_import_items.insert_one(item.model_dump())

    response = {
        "job_id": job.id,
        "status": job.status,
        "total_found": job.total_found,
        "total_errors": job.total_errors,
        "total_warnings": job.total_warnings,
    }

    return JSONResponse(status_code=200, content=response)
