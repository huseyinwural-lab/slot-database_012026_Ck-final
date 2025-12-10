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
    RtpCountryOverride,
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
    JackpotConfig,
    JackpotConfigResponse,
    JackpotPool,
    GameAsset,
    GameAssetsResponse,
    PokerRules,
    PokerRulesResponse,
    CrashMathConfig,
    CrashMathConfigResponse,
    DiceMathConfig,
    DiceMathConfigResponse,
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


class PokerRulesSaveRequest(BaseModel):
    variant: str
    limit_type: str
    min_players: int
    max_players: int
    min_buyin_bb: float
    max_buyin_bb: float
    rake_type: str  # "percentage", "time", "none"
    rake_percent: Optional[float] = None
    rake_cap_currency: Optional[float] = None
    rake_applies_from_pot: Optional[float] = None
    use_antes: bool = False
    ante_bb: Optional[float] = None
    small_blind_bb: float
    big_blind_bb: float
    allow_straddle: bool = False
    run_it_twice_allowed: bool = False
    min_players_to_start: int

    # --- Branding ---
    table_label: Optional[str] = None
    theme: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None

    # --- Behavior ---
    auto_muck_enabled: Optional[bool] = False
    auto_rebuy_enabled: Optional[bool] = False
    auto_rebuy_threshold_bb: Optional[int] = None
    sitout_time_limit_seconds: Optional[int] = 120
    disconnect_wait_seconds: Optional[int] = 30
    late_entry_enabled: Optional[bool] = False

    # --- Anti-Collusion & Safety ---
    max_same_country_seats: Optional[int] = None
    block_vpn_flagged_players: Optional[bool] = False
    session_max_duration_minutes: Optional[int] = None
    max_daily_buyin_limit_bb: Optional[int] = None

    summary: Optional[str] = None


class CrashMathSaveRequest(BaseModel):
    base_rtp: float
    volatility_profile: str
    min_multiplier: float
    max_multiplier: float
    max_auto_cashout: float
    round_duration_seconds: int
    bet_phase_seconds: int
    grace_period_seconds: int
    min_bet_per_round: Optional[float] = None
    max_bet_per_round: Optional[float] = None
    provably_fair_enabled: bool
    rng_algorithm: str
    seed_rotation_interval_rounds: Optional[int] = None
    summary: Optional[str] = None


class DiceMathSaveRequest(BaseModel):
    range_min: float
    range_max: float
    step: float
    house_edge_percent: float
    min_payout_multiplier: float
    max_payout_multiplier: float
    allow_over: bool
    allow_under: bool
    min_target: float
    max_target: float
    round_duration_seconds: int
    bet_phase_seconds: int
    provably_fair_enabled: bool
    rng_algorithm: str
    seed_rotation_interval_rounds: Optional[int] = None
    summary: Optional[str] = None


def _crash_math_error(message: str, field: str, value: Any = None, reason: str = "invalid") -> Dict[str, Any]:
    details: Dict[str, Any] = {"field": field, "reason": reason}
    if value is not None:
        details["value"] = value
    return {"error_code": "CRASH_MATH_VALIDATION_FAILED", "message": message, "details": details}

# ... REST OF FILE UNCHANGED ...
