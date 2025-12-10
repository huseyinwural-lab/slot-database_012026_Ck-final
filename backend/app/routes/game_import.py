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
from app.models.game import (
    GameConfigVersion,
    GameConfigVersionStatus,
    GameLog,
    PaytableRecord,
    ReelStripsRecord,
)
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
    latest = (
        await db.game_config_versions
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )
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
    """Handle manual game import via JSON or ZIP bundle.

    This endpoint only performs parsing + validation and creates a GameImportJob + GameImportItem.
    Actual import into games/config collections is handled by /jobs/{job_id}/import.
    """
    db = get_db()
    admin_id = "current_admin"  # TODO: integrate real auth
    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    filename = file.filename or "upload.bin"
    content = await file.read()

    # --- Parse file ---
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

    # --- Extract minimal metadata ---
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
    existing_game = await db.games.find_one({"provider_game_id": game_id}, {"_id": 0})
    already_exists = bool(existing_game)
    if already_exists:
        errors.append("Game with this game_id / provider_game_id already exists")

    # --- Create import job ---
    job = GameImportJob(
        provider=payload.get("provider"),
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
                "source_label": source_label,
                "notes": notes,
                "errors": errors,
                "warnings": warnings,
            }
        ],
    )

    await db.game_import_jobs.insert_one(job.model_dump())

    item_status = "ready" if not errors and not already_exists else "error"

    item = GameImportItem(
        job_id=job.id,
        provider=payload.get("provider"),
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


@router.get("/jobs/{job_id}")
async def get_import_job(job_id: str):
    """Return job summary plus associated items for preview UI."""
    db = get_db()
    job_doc = await db.game_import_jobs.find_one({"id": job_id}, {"_id": 0})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Import job not found")

    items = await db.game_import_items.find({"job_id": job_id}, {"_id": 0}).to_list(100)

    # raw_payload büyük olabileceği için preview'de göndermiyoruz
    for it in items:
        if "raw_payload" in it:
            it["has_raw_payload"] = True
            it.pop("raw_payload")

    return {"job": job_doc, "items": items}


@router.post("/jobs/{job_id}/import")
async def import_job(job_id: str, request: Request):
    """Import READY items for a job into games + config collections.

    İlk sürümde sadece category == "slot" için temel import yapılır.
    Diğer kategoriler için item error'a çekilir ve job completed with errors olur.
    """
    db = get_db()
    admin_id = "current_admin"  # TODO: real auth
    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    job_doc = await db.game_import_jobs.find_one({"id": job_id}, {"_id": 0})
    if not job_doc:
        raise HTTPException(status_code=404, detail="Import job not found")

    items_docs = await db.game_import_items.find({"job_id": job_id}, {"_id": 0}).to_list(100)
    if not items_docs:
        raise HTTPException(status_code=400, detail="No items found for this job")

    imported_count = 0
    error_count = 0

    for it in items_docs:
        item = GameImportItem(**it)

        if item.status != "ready":
            continue

        payload = item.raw_payload or {}
        category = (item.category or "").lower()

        # Şimdilik sadece slot oyunları destekleniyor
        if category != "slot":
            item.errors.append("Manual import pipeline currently supports only slot games.")
            item.status = "error"
            error_count += 1
            await db.game_import_items.update_one(
                {"id": item.id},
                {"$set": {"status": item.status, "errors": item.errors}},
            )
            continue

        # Son kontrol: aynı provider_game_id tekrar oluşmuş mu?
        existing = await db.games.find_one({"provider_game_id": item.provider_game_id}, {"_id": 0})
        if existing:
            item.errors.append("Game already exists at import time.")
            item.status = "error"
            error_count += 1
            await db.game_import_items.update_one(
                {"id": item.id},
                {"$set": {"status": item.status, "errors": item.errors, "already_exists": True}},
            )
            continue

        try:
            # --- Create Game entry ---
            new_game = Game(
                name=item.name,
                provider=payload.get("provider") or (job_doc.get("provider") or "Manual"),
                category=item.category,
                core_type=payload.get("core_type"),
            )
            new_game.provider_game_id = item.provider_game_id

            await db.games.insert_one(new_game.model_dump())

            # --- Config version ---
            version = await _generate_new_version(
                db,
                new_game.id,
                admin_id,
                notes=f"Imported via manual job {job_id}",
            )

            config = payload.get("config") or {}

            # Paytable
            if "paytable" in config:
                pay_rec = PaytableRecord(
                    game_id=new_game.id,
                    config_version_id=version.id,
                    data=config["paytable"],
                    source="import",
                    created_by=admin_id,
                )
                await db.paytables.insert_one(pay_rec.model_dump())

            # Reel strips
            if "reels" in config:
                reels_rec = ReelStripsRecord(
                    game_id=new_game.id,
                    config_version_id=version.id,
                    data=config["reels"],
                    created_by=admin_id,
                    source="import",
                )
                await db.reel_strips.insert_one(reels_rec.model_dump())

            # TODO: jackpots, bets, features, assets vs. ileriki iterasyonlarda eklenecek

            item.status = "imported"
            await db.game_import_items.update_one(
                {"id": item.id}, {"$set": {"status": item.status}}
            )

            imported_count += 1

            await _append_game_log(
                db,
                new_game.id,
                admin_id,
                "game_import_manual_imported",
                {
                    "job_id": job_id,
                    "request_id": request_id,
                    "provider_game_id": item.provider_game_id,
                },
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Failed to import game from manual job %s", job_id)
            item.errors.append(f"Unexpected error during import: {exc}")
            item.status = "error"
            error_count += 1
            await db.game_import_items.update_one(
                {"id": item.id},
                {"$set": {"status": item.status, "errors": item.errors}},
            )

    # --- Update job summary ---
    new_status = "completed" if imported_count > 0 and error_count == 0 else "failed"

    await db.game_import_jobs.update_one(
        {"id": job_id},
        {
            "$set": {
                "status": new_status,
                "total_imported": imported_count,
                "total_errors": job_doc.get("total_errors", 0) + error_count,
                "completed_at": datetime.now(timezone.utc),
            },
            "$push": {
                "logs": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": "game_import_manual_imported",
                    "request_id": request_id,
                    "imported_count": imported_count,
                    "additional_errors": error_count,
                }
            },
        },
    )

    return {
        "message": f"Imported {imported_count} item(s) with {error_count} additional error(s).",
        "imported": imported_count,
        "errors": error_count,
        "job_status": new_status,
    }
