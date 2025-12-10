from fastapi import APIRouter, HTTPException, Body, Query, Request
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
from uuid import uuid4

from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient

from config import settings
from app.models.core import Game, GameConfig, ApprovalRequest, ApprovalCategory
from app.models.game import (
    GameConfigVersion,
    GameConfigVersionStatus,
    RtpProfile,
    RtpConfigResponse,
    BetConfig,
    BetConfigResponse,
    GameFeatureFlags,
    GameFeatureFlagsResponse,
    GameGeneralConfig,
    GameLog,
    GameLogsResponse,
    PaytableRecord,
    PaytableHistoryItem,
    PaytableResponse,
    ReelStripsRecord,
    ReelStripsHistoryItem,
    ReelStripsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/games", tags=["games_config"])


def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]


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
    # Update game with current_config_version_id (stored as extra field)
    await db.games.update_one({"id": game_id}, {"$set": {"current_config_version_id": version.id}})
    return version


async def _append_game_log(db, game_id: str, admin_id: str, action: str, details: Dict[str, Any]):
    log = GameLog(game_id=game_id, admin_id=admin_id, action=action, details=details)
    await db.game_logs.insert_one(log.model_dump())


def _paytable_error(message: str, field: str, reason: str, code: str = "PAYTABLE_VALIDATION_FAILED") -> Dict[str, Any]:
    return {
        "error_code": code,
        "message": message,
        "details": {
            "field": field,
            "reason": reason,
        },
    }

    # NOTE: game_config specific helper errors are standardised per domain (paytable, reel_strips, etc.)


class PaytableValidationError(Exception):
    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload


@router.get("/{game_id}/config/general", response_model=GameGeneralConfig)
async def get_game_general_config(game_id: str):
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    game = Game(**game_doc)
    visibility = game_doc.get("visibility_rules", {}) or {}

    status = str(game.business_status)
    # Map BusinessStatus to simple status string
    # BusinessStatus.ACTIVE -> active, others -> inactive by default
    simple_status = "active" if status.endswith("ACTIVE") or status == "active" else "inactive"

    return GameGeneralConfig(
        name=game.name,
        provider=game.provider,
        category=game.category,
        default_language=game_doc.get("default_language", "en"),
        visibility_rules=visibility,
        lobby_sort_order=game_doc.get("lobby_sort_order", game.sort_order or 0),
        tags=game.tags or [],
        status=simple_status,
    )


@router.post("/{game_id}/config/general")
async def update_game_general_config(game_id: str, payload: GameGeneralConfig):
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
    # TODO: game_level lock for general config can be added similarly to paytable/reel strips if needed

        raise HTTPException(status_code=404, detail="Game not found")

    admin_id = "current_admin"  # TODO: hook into auth when available
    old_status = game_doc.get("business_status", "draft")

    # Map simple status back to BusinessStatus enum string
    new_business_status = "active" if payload.status == "active" else "suspended"

    update_data: Dict[str, Any] = {
        "name": payload.name,
        "provider": payload.provider,
        "category": payload.category,
        "default_language": payload.default_language,
        "visibility_rules": payload.visibility_rules.model_dump(),
        "lobby_sort_order": payload.lobby_sort_order,
        "sort_order": payload.lobby_sort_order,
        "tags": payload.tags,
        "business_status": new_business_status,
        "updated_at": datetime.now(timezone.utc),
    }

    await db.games.update_one({"id": game_id}, {"$set": update_data})

    details = {"fields": list(update_data.keys())}
    if old_status != new_business_status:
        details["status_change"] = {"old": old_status, "new": new_business_status}

    await _append_game_log(db, game_id, admin_id, "general_update", details)
    return {"message": "Game general config updated"}


@router.get("/{game_id}/config/rtp", response_model=RtpConfigResponse)
async def get_game_rtp_config(game_id: str):
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    profiles_docs = await db.rtp_profiles.find({"game_id": game_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    profiles = [RtpProfile(**p) for p in profiles_docs]

    default_profile_id = game_doc.get("default_rtp_profile_id")
    if not default_profile_id and profiles:
        # pick first marked as default or most recent
        default = next((p for p in profiles if p.is_default), profiles[0])
        default_profile_id = default.id

    return RtpConfigResponse(game_id=game_id, default_profile_id=default_profile_id, profiles=profiles)


class RtpProfileCreate(RtpProfile):
    class Config:
        extra = "ignore"


@router.post("/{game_id}/config/rtp", response_model=RtpProfile)
async def create_rtp_profile(game_id: str, payload: RtpProfileCreate):
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    admin_id = "current_admin"
    version = await _generate_new_version(db, game_id, admin_id, notes="RTP profile change")

    profile = RtpProfile(
        game_id=game_id,
        config_version_id=version.id,
        code=payload.code,
        rtp_value=payload.rtp_value,
        is_default=payload.is_default,
        country_overrides=payload.country_overrides,
    )

    await db.rtp_profiles.insert_one(profile.model_dump())

    # Update default RTP profile on game if needed
    if profile.is_default:
        await db.games.update_one({"id": game_id}, {"$set": {"default_rtp_profile_id": profile.id}})

    # Create approval request for RTP change
    approval = ApprovalRequest(
        category=ApprovalCategory.GAME,
        action_type="rtp_change",
        related_entity_id=game_id,
        requester_admin=admin_id,
        amount=None,
    # Validation for bet config errors could be normalised as well if needed

        details={"rtp_code": profile.code, "rtp_value": profile.rtp_value},
    )
    db_ = get_db()
    await db_.approvals.insert_one(approval.model_dump())

    await _append_game_log(db, game_id, admin_id, "rtp_profile_created", {"profile_id": profile.id})

    return profile


@router.get("/{game_id}/config/bets", response_model=BetConfigResponse)
async def get_bet_config(game_id: str):
    db = get_db()
    cfg_docs = await db.bet_configs.find({"game_id": game_id}, {"_id": 0}).sort("created_at", -1).limit(1).to_list(1)
    config = BetConfig(**cfg_docs[0]) if cfg_docs else None
    return BetConfigResponse(game_id=game_id, config=config)


@router.post("/{game_id}/config/bets", response_model=BetConfig)
async def save_bet_config(game_id: str, payload: BetConfig):
    if payload.min_bet >= payload.max_bet:
        raise HTTPException(status_code=400, detail="min_bet must be less than max_bet")

    for p in payload.presets:
        if p < payload.min_bet or p > payload.max_bet:
            raise HTTPException(status_code=400, detail="All presets must be within min/max range")

    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    admin_id = "current_admin"
    version = await _generate_new_version(db, game_id, admin_id, notes="Bet config change")

    config = BetConfig(
        id=payload.id or None,
        game_id=game_id,
        config_version_id=version.id,
        min_bet=payload.min_bet,
        max_bet=payload.max_bet,
        step=payload.step,
        presets=payload.presets,
        country_overrides=payload.country_overrides,
    )

    await db.bet_configs.insert_one(config.model_dump())
    await _append_game_log(db, game_id, admin_id, "bet_config_saved", {"config_id": config.id})

    # Also update base game configuration for quick filters
    await db.games.update_one(
        {"id": game_id},
        {"$set": {"configuration.min_bet": config.min_bet, "configuration.max_bet": config.max_bet}},
    )

    return config


@router.get("/{game_id}/config/features", response_model=GameFeatureFlagsResponse)
async def get_feature_flags(game_id: str):
    db = get_db()
    docs = await db.game_feature_flags.find({"game_id": game_id}, {"_id": 0}).sort("created_at", -1).limit(1).to_list(1)
    if docs:
        flags = GameFeatureFlags(**docs[0])
        return GameFeatureFlagsResponse(game_id=game_id, features=flags.features)

    # Fallback: infer from base game configuration
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    conf = game_doc.get("configuration", {}) or {}
    base_features = {
        "bonus_buy": bool(conf.get("bonus_buy_enabled", False)),
        "turbo_spin": False,
        "autoplay": True,
    }
    return GameFeatureFlagsResponse(game_id=game_id, features=base_features)


class GameFeatureFlagsUpdate(GameFeatureFlagsResponse):
    class Config:
        extra = "ignore"


@router.post("/{game_id}/config/features", response_model=GameFeatureFlagsResponse)
async def save_feature_flags(game_id: str, payload: GameFeatureFlagsUpdate):
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    admin_id = "current_admin"
    # NOTE: paytable-specific validation and errors live below

    version = await _generate_new_version(db, game_id, admin_id, notes="Feature flags change")

    flags = GameFeatureFlags(
        game_id=game_id,
        config_version_id=version.id,
        features=payload.features,
    )
    await db.game_feature_flags.insert_one(flags.model_dump())

    # Also update base game configuration where possible
    await db.games.update_one(
        {"id": game_id},
        {"$set": {"configuration.bonus_buy_enabled": bool(payload.features.get("bonus_buy", False))}},
    )

    await _append_game_log(db, game_id, admin_id, "feature_flags_saved", {"features": payload.features})
    return GameFeatureFlagsResponse(game_id=game_id, features=payload.features)


@router.get("/{game_id}/config/paytable", response_model=PaytableResponse)
async def get_paytable(game_id: str, request: Request):
    """Return current paytable and short history for a game."""
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    # Latest as current
    latest_docs = (
        await db.paytables
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )
    current = PaytableRecord(**latest_docs[0]) if latest_docs else None

    # History (last 10)
    history_docs = (
        await db.paytables
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(10)
        .to_list(10)
    )
    history_items = [
        PaytableHistoryItem(
            config_version_id=d["config_version_id"],
            source=d.get("source", "provider"),
            created_at=d["created_at"],
            created_by=d.get("created_by", "system"),
            summary=d.get("summary"),
        )
        for d in history_docs
    ]

    if current:
        logger.info(
            "paytable_get",
            extra={
                "game_id": game_id,
                "config_version_id": current.config_version_id,
                "admin_id": "n/a",
                "request_id": request_id,
                "action_type": "paytable_get",
            },
        )

    return PaytableResponse(current=current, history=history_items)


class PaytableOverrideRequest(BaseModel):
    data: Dict[str, Any]
    summary: Optional[str] = None


def _validate_paytable_payload(data: Dict[str, Any]):
    symbols = data.get("symbols")
    if not isinstance(symbols, list) or not symbols:
        raise PaytableValidationError(_paytable_error("symbols alanı zorunludur.", "data.symbols", "missing"))

    for sym in symbols:
        code = sym.get("code")
        pays = sym.get("pays")
        if not code:
            raise PaytableValidationError(_paytable_error("Her sembol için 'code' zorunludur.", "data.symbols[].code", "missing"))
        if not isinstance(pays, dict):
            raise PaytableValidationError(
                _paytable_error("Her sembol için pays objesi zorunludur.", "data.symbols[].pays", "invalid_type"),
            )
        for k, v in pays.items():
            try:
                val = float(v)
            except Exception:
                raise PaytableValidationError(
                    _paytable_error(
                        f"{code} için {k}x değeri sayısal olmalıdır.",
                        f"data.symbols[].pays.{k}",
                        "invalid_number",
                    )
                )
            if val < 0:
                raise PaytableValidationError(
                    _paytable_error(
                        f"{code} için {k}x ödemesi 0'dan küçük olamaz.",
                        f"data.symbols[].pays.{k}",
                        "negative",
                    )
                )

    lines = data.get("lines")
    if lines is not None and (not isinstance(lines, int) or lines < 1):
        raise PaytableValidationError(
            _paytable_error("lines en az 1 olmalıdır.", "data.lines", "invalid"),
        )


# --- REEL STRIPS CONFIG ---

class ReelStripsValidationError(Exception):
    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload


def _reel_error(message: str, field: str, reason: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "error_code": "REEL_STRIPS_VALIDATION_FAILED",
        "message": message,
        "details": {
            "field": field,
            "reason": reason,
        },
    }
    if extra:
        base["details"].update(extra)
    return base


def _validate_reel_strips_payload(data: Dict[str, Any]):
    layout = data.get("layout") or {}
    reels_count = layout.get("reels")
    if not isinstance(reels_count, int) or reels_count < 1:
        raise ReelStripsValidationError(
            _reel_error("layout.reels en az 1 olmalıdır.", "data.layout.reels", "invalid"),
        )

    reels = data.get("reels")
    if not isinstance(reels, list) or not reels:
        raise ReelStripsValidationError(
            _reel_error("data.reels zorunludur ve boş olamaz.", "data.reels", "missing"),
        )

    if len(reels) != reels_count:
        raise ReelStripsValidationError(
            _reel_error(
                "Reel sayısı ile layout.reels eşleşmiyor.",
                "data.reels",
                "count_mismatch",
                {"expected": reels_count, "actual": len(reels)},
            ),
        )

    for idx, reel in enumerate(reels):
        if not isinstance(reel, list) or not reel:
            raise ReelStripsValidationError(
                _reel_error(
                    "Her reel non-empty array olmalıdır.",
                    f"data.reels[{idx}]",
                    "invalid",
                ),
            )
        for sym in reel:
            if not isinstance(sym, str) or not sym.strip():
                raise ReelStripsValidationError(
                    _reel_error(
                        "Tüm semboller non-empty string olmalıdır.",
                        f"data.reels[{idx}]",
                        "invalid_symbol",
                    ),
                )


@router.get("/{game_id}/config/reel-strips", response_model=ReelStripsResponse)
async def get_reel_strips(game_id: str, request: Request):
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    latest_docs = (
        await db.reel_strips
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )
    current = ReelStripsRecord(**latest_docs[0]) if latest_docs else None

    history_docs = (
        await db.reel_strips
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(10)
        .to_list(10)
    )
    history_items = [
        ReelStripsHistoryItem(
            config_version_id=d["config_version_id"],
            schema_version=d.get("schema_version", "1.0.0"),
            source=d.get("source", "manual"),
            created_at=d["created_at"],
            created_by=d.get("created_by", "system"),
            summary=d.get("summary"),
        )
        for d in history_docs
    ]

    if current:
        logger.info(
            "reel_strips_read",
            extra={
                "game_id": game_id,
                "config_version_id": current.config_version_id,
                "admin_id": "n/a",
                "request_id": request_id,
                "action_type": "reel_strips_read",
            },
        )

    return ReelStripsResponse(current=current, history=history_items)


class ReelStripsSaveRequest(BaseModel):
    data: Dict[str, Any]
    source: str = "manual"
    summary: Optional[str] = None


@router.post("/{game_id}/config/reel-strips", response_model=ReelStripsRecord)
async def save_reel_strips(game_id: str, payload: ReelStripsSaveRequest, request: Request):
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    # Hook for future math lock
    if game_doc.get("is_locked_for_math_changes"):
        from fastapi.responses import JSONResponse

        error_payload = _reel_error(
            "Bu oyun için math değişiklikleri kilitlidir.",
            "game.is_locked_for_math_changes",
            "locked",
        )
        return JSONResponse(status_code=403, content=error_payload)

    try:
        _validate_reel_strips_payload(payload.data)
    except ReelStripsValidationError as exc:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=400, content=exc.payload)

    admin_id = "current_admin"
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    version = await _generate_new_version(db, game_id, admin_id, notes="Reel strips change")

    record = ReelStripsRecord(
        game_id=game_id,
        config_version_id=version.id,
        data=payload.data,
        schema_version="1.0.0",
        created_by=admin_id,
        source=payload.source or "manual",
    )

    doc = record.model_dump()
    doc["summary"] = payload.summary or "Reel strips saved"
    await db.reel_strips.insert_one(doc)

    details = {
        "config_version_id": version.id,
        "summary": payload.summary,
        "game_id": game_id,
        "admin_id": admin_id,
        "request_id": request_id,
        "action_type": "reel_strips_saved",
    }

    await _append_game_log(db, game_id, admin_id, "reel_strips_saved", details)

    logger.info(
        "reel_strips_saved",
        extra={
            "game_id": game_id,
            "config_version_id": version.id,
            "admin_id": admin_id,
            "request_id": request_id,
            "action_type": "reel_strips_saved",
        },
    )

    # Optional approval hook
    approval = ApprovalRequest(
        category=ApprovalCategory.GAME,
        action_type="reel_strips_change",
        related_entity_id=game_id,
        requester_admin=admin_id,
        details={"config_version_id": version.id, "summary": payload.summary},
    )
    await db.approvals.insert_one(approval.model_dump())

    return record


class ReelStripsImportRequest(BaseModel):
    format: str  # "json" | "csv"
    content: str


@router.post("/{game_id}/config/reel-strips/import", response_model=ReelStripsRecord)
async def import_reel_strips(game_id: str, payload: ReelStripsImportRequest, request: Request):
    """Basic import hook for JSON/CSV; currently supports JSON and a very simple CSV format."""
    from fastapi.responses import JSONResponse

    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    # Future math lock
    if game_doc.get("is_locked_for_math_changes"):
        error_payload = _reel_error(
            "Bu oyun için math değişiklikleri kilitlidir.",
            "game.is_locked_for_math_changes",
            "locked",
        )
        return JSONResponse(status_code=403, content=error_payload)

    fmt = (payload.format or "json").lower()
    parsed_data: Dict[str, Any]

    try:
        if fmt == "json":
            parsed_data = __import__("json").loads(payload.content)
        elif fmt == "csv":
            # Very naive CSV parser: each line is a reel, symbols separated by commas
            lines = [line.strip() for line in payload.content.splitlines() if line.strip()]
            reels = [line.split(",") for line in lines]
            parsed_data = {
                "layout": {"reels": len(reels), "rows": None},
                "reels": reels,
            }
        else:
            error_payload = _reel_error("Unsupported format", "format", "unsupported", {"supported": ["json", "csv"]})
            return JSONResponse(status_code=400, content=error_payload)
    except Exception:
        error_payload = _reel_error("Import içeriği parse edilemedi.", "content", "parse_error")
        return JSONResponse(status_code=400, content=error_payload)

    try:
        _validate_reel_strips_payload(parsed_data)
    except ReelStripsValidationError as exc:
        return JSONResponse(status_code=400, content=exc.payload)

    # Reuse save logic by directly inserting
    admin_id = "current_admin"
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    version = await _generate_new_version(db, game_id, admin_id, notes="Reel strips import")

    record = ReelStripsRecord(
        game_id=game_id,
        config_version_id=version.id,
        data=parsed_data,
        schema_version="1.0.0",
        created_by=admin_id,
        source="import",
    )

    doc = record.model_dump()
    doc["summary"] = "Imported via API"
    await db.reel_strips.insert_one(doc)

    details = {
        "config_version_id": version.id,
        "game_id": game_id,
        "admin_id": admin_id,
        "request_id": request_id,
        "action_type": "reel_strips_imported",
    }

    await _append_game_log(db, game_id, admin_id, "reel_strips_imported", details)

    logger.info(
        "reel_strips_imported",
        extra={
            "game_id": game_id,
            "config_version_id": version.id,
            "admin_id": admin_id,
            "request_id": request_id,
            "action_type": "reel_strips_imported",
        },
    )

    return record


class ReelStripsSimulateRequest(BaseModel):
    rounds: int = 10000
    bet: float = 1.0


@router.post("/{game_id}/config/reel-strips/simulate")
async def simulate_reel_strips(game_id: str, payload: ReelStripsSimulateRequest, request: Request):
    """Stub endpoint for triggering math simulation based on current reel strips."""
    from fastapi.responses import JSONResponse

    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    admin_id = "current_admin"

    # In future this would enqueue a job to a simulation service
    simulation_id = str(uuid4())

    details = {
        "simulation_id": simulation_id,
        "rounds": payload.rounds,
        "bet": payload.bet,
        "game_id": game_id,
        "admin_id": admin_id,
        "request_id": request_id,
        "action_type": "reel_strips_simulate_triggered",
    }

    await _append_game_log(db, game_id, admin_id, "reel_strips_simulate_triggered", details)

    logger.info(
        "reel_strips_simulate_triggered",
        extra=details,
    )

    return JSONResponse(
        status_code=200,
        content={"status": "queued", "simulation_id": simulation_id},
    )


                        f"data.symbols[].pays.{k}",
                        "negative",
                    )
                )


@router.post("/{game_id}/config/paytable/override", response_model=PaytableRecord)
async def save_paytable_override(game_id: str, payload: PaytableOverrideRequest, request: Request):
    """Save a new override paytable version for a game."""
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    # Hook for future lock logic
    if game_doc.get("is_locked_for_math_changes"):
        from fastapi.responses import JSONResponse

        error_payload = _paytable_error(
            "Bu oyun için math değişiklikleri kilitlidir.",
            "game.is_locked_for_math_changes",
            "locked",
            code="PAYTABLE_LOCKED",
        )
        return JSONResponse(status_code=403, content=error_payload)

    try:
        _validate_paytable_payload(payload.data)
    except PaytableValidationError as exc:
        # Standard error format for validation
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=400, content=exc.payload)

    admin_id = "current_admin"
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    version = await _generate_new_version(db, game_id, admin_id, notes="Paytable override change")

    record = PaytableRecord(
        game_id=game_id,
        config_version_id=version.id,
        data=payload.data,
        source="override",
        created_by=admin_id,
    )

    doc = record.model_dump()
    doc["summary"] = payload.summary or "Paytable override saved"
    await db.paytables.insert_one(doc)

    details = {
        "config_version_id": version.id,
        "summary": payload.summary,
        "request_id": request_id,
        "action_type": "paytable_override",
        "game_id": game_id,
        "admin_id": admin_id,
    }

    await _append_game_log(
        db,
        game_id,
        admin_id,
        "paytable_override_saved",
        details,
    )

    logger.info(
        "paytable_override_saved",
        extra={
            "game_id": game_id,
            "config_version_id": version.id,
            "admin_id": admin_id,
            "request_id": request_id,
            "action_type": "paytable_override",
        },
    )

    # Optional: create approval request
    approval = ApprovalRequest(
        category=ApprovalCategory.GAME,
        action_type="paytable_change",
        related_entity_id=game_id,
        requester_admin=admin_id,
        details={"config_version_id": version.id, "summary": payload.summary},
    )
    await db.approvals.insert_one(approval.model_dump())

    return record


@router.post("/{game_id}/config/paytable/refresh-from-provider")
async def refresh_paytable_from_provider(game_id: str, request: Request):
    """Stub endpoint to simulate fetching paytable from provider."""
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    # Hook for future lock logic
    if game_doc.get("is_locked_for_math_changes"):
        from fastapi.responses import JSONResponse

        error_payload = _paytable_error(
            "Bu oyun için math değişiklikleri kilitlidir.",
            "game.is_locked_for_math_changes",
            "locked",
            code="PAYTABLE_LOCKED",
        )
        return JSONResponse(status_code=403, content=error_payload)

    admin_id = "system_provider_stub"
    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    # Simple stub: create a mock provider paytable
    mock_data = {
        "symbols": [
            {"code": "A", "pays": {"3": 5, "4": 10, "5": 20}},
            {"code": "K", "pays": {"3": 4, "4": 8, "5": 16}},
        ],
        "lines": 20,
        "specials": {"wild": "WILD", "scatter": "SCATTER"},
    }

    version = await _generate_new_version(db, game_id, admin_id, notes="Paytable refresh from provider (stub)")

    record = PaytableRecord(
        game_id=game_id,
        config_version_id=version.id,
        data=mock_data,
        source="provider",
        created_by="system",
    )

    doc = record.model_dump()
    doc["summary"] = "Refreshed from provider (stub)"
    await db.paytables.insert_one(doc)

    details = {
        "config_version_id": version.id,
        "request_id": request_id,
        "action_type": "paytable_refresh",
        "game_id": game_id,
        "admin_id": admin_id,
    }

    await _append_game_log(
        db,
        game_id,
        admin_id,
        "paytable_refreshed_from_provider",
        details,
    )

    logger.info(
        "paytable_refreshed_from_provider",
        extra={
            "game_id": game_id,
            "config_version_id": version.id,
            "admin_id": admin_id,
            "request_id": request_id,
            "action_type": "paytable_refresh",
        },
    )

    return {"message": "Paytable refreshed from provider (stub)", "config_version_id": version.id}


@router.get("/{game_id}/config/logs", response_model=GameLogsResponse)
async def get_game_logs(game_id: str, limit: int = Query(50, ge=1, le=200)):
    db = get_db()
    docs = (
        await db.game_logs.find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(limit)
        .to_list(length=limit)
    )
    logs = [GameLog(**d) for d in docs]
    return GameLogsResponse(items=logs)
