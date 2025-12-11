from fastapi import APIRouter, HTTPException, Body, Query, Request
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
import logging
from uuid import uuid4

from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from enum import Enum

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
    BlackjackRules,
    BlackjackRulesResponse,
    SlotAdvancedConfig,
    SlotAdvancedConfigResponse,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/games", tags=["games_config"])



class ValidationReason(str, Enum):
    MUST_BE_POSITIVE = "must_be_positive"
    INVALID_COUNTRY_CODE = "invalid_country_code"
    UNSUPPORTED_ENFORCEMENT_MODE = "unsupported_enforcement_mode"


def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]


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
    # Update game with current_config_version_id (stored as extra field)
    await db.games.update_one({"id": game_id}, {"$set": {"current_config_version_id": version.id}})
    return version


async def _append_game_log(db, game_id: str, admin_id: str, action: str, details: Dict[str, Any]):
    log = GameLog(game_id=game_id, admin_id=admin_id, action=action, details=details)
    await db.game_logs.insert_one(log.model_dump())


# ---------------------------------------------------------------------------
# GENERAL CONFIG
# ---------------------------------------------------------------------------


def _paytable_error(message: str, field: str, reason: str, code: str = "PAYTABLE_VALIDATION_FAILED") -> Dict[str, Any]:
    return {
        "error_code": code,
        "message": message,
        "details": {
            "field": field,
            "reason": reason,
        },
    }


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


# ---------------------------------------------------------------------------
# POKER / CRASH / DICE CONFIG SAVE REQUEST MODELS
# ---------------------------------------------------------------------------


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

    # Advanced safety limits (global, optional)
    max_loss_per_round: Optional[float] = None
    max_win_per_round: Optional[float] = None
    max_rounds_per_session: Optional[int] = None
    max_total_loss_per_session: Optional[float] = None
    max_total_win_per_session: Optional[float] = None

    enforcement_mode: Optional[str] = None

    # Country specific overrides keyed by ISO 3166-1 alpha-2 country code
    # Example:
    # {"TR": {"max_total_loss_per_session": 1000, "max_total_win_per_session": 5000}}
    country_overrides: Optional[Dict[str, Dict[str, Any]]] = None

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

    # Advanced limits (global, optional)
    max_win_per_bet: Optional[float] = None
    max_loss_per_bet: Optional[float] = None
    max_session_loss: Optional[float] = None
    max_session_bets: Optional[int] = None

    enforcement_mode: Optional[str] = None

    # Country specific overrides keyed by ISO 3166-1 alpha-2 country code
    country_overrides: Optional[Dict[str, Dict[str, Any]]] = None

    # Provably fair settings
    provably_fair_enabled: bool = True
    rng_algorithm: str = "sha256_chain"
    seed_rotation_interval_rounds: Optional[int] = None
    summary: Optional[str] = None


class SlotAdvancedSaveRequest(BaseModel):
    spin_speed: str
    turbo_spin_allowed: bool = False
    autoplay_enabled: bool = True
    autoplay_default_spins: int
    autoplay_max_spins: int
    autoplay_stop_on_big_win: bool = True
    autoplay_stop_on_balance_drop_percent: Optional[float] = None
    big_win_animation_enabled: bool = True
    gamble_feature_allowed: bool = False
    summary: Optional[str] = None


class BlackjackRulesSaveRequest(BaseModel):
    deck_count: int
    dealer_hits_soft_17: bool
    blackjack_payout: float
    double_allowed: bool
    double_after_split_allowed: bool
    split_max_hands: int
    resplit_aces_allowed: bool
    surrender_allowed: bool
    insurance_allowed: bool
    min_bet: float
    max_bet: float
    side_bets_enabled: bool = False
    side_bets: Optional[List[Dict[str, Any]]] = None
    table_label: Optional[str] = None
    theme: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    auto_seat_enabled: Optional[bool] = False
    sitout_time_limit_seconds: Optional[int] = 120
    disconnect_wait_seconds: Optional[int] = 30
    max_same_country_seats: Optional[int] = None
    block_vpn_flagged_players: Optional[bool] = False
    session_max_duration_minutes: Optional[int] = None
    max_daily_buyin_limit: Optional[float] = None
    summary: Optional[str] = None


# ---------------------------------------------------------------------------
# CRASH MATH CONFIG
# ---------------------------------------------------------------------------


from enum import Enum


def _crash_math_error(message: str, field: str, value: Any = None, reason: str = "invalid") -> Dict[str, Any]:
    details: Dict[str, Any] = {"field": field, "reason": reason}
    if value is not None:
        details["value"] = value
    return {"error_code": "CRASH_MATH_VALIDATION_FAILED", "message": message, "details": details}


@router.get("/{game_id}/config/crash-math", response_model=CrashMathConfigResponse)
async def get_crash_math_config(game_id: str, request: Request):
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    core_type = game_doc.get("core_type") or game_doc.get("coreType")
    if core_type != "CRASH":
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=404,
            content={
                "error_code": "CRASH_MATH_NOT_AVAILABLE_FOR_GAME",
                "message": "Crash math configuration is only available for CRASH games.",
            },
        )

    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    docs = (
        await db.crash_math_configs
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )

    if docs:
        cfg = CrashMathConfig(**docs[0])
        response = CrashMathConfigResponse(
            config_version_id=cfg.config_version_id,
            schema_version=cfg.schema_version,
            base_rtp=cfg.base_rtp,
            volatility_profile=cfg.volatility_profile,
            min_multiplier=cfg.min_multiplier,
            max_multiplier=cfg.max_multiplier,
            max_auto_cashout=cfg.max_auto_cashout,
            round_duration_seconds=cfg.round_duration_seconds,
            bet_phase_seconds=cfg.bet_phase_seconds,
            grace_period_seconds=cfg.grace_period_seconds,
            min_bet_per_round=cfg.min_bet_per_round,
            max_bet_per_round=cfg.max_bet_per_round,
            max_loss_per_round=cfg.max_loss_per_round,
            max_win_per_round=cfg.max_win_per_round,
            max_rounds_per_session=cfg.max_rounds_per_session,
            max_total_loss_per_session=cfg.max_total_loss_per_session,
            max_total_win_per_session=cfg.max_total_win_per_session,
            enforcement_mode=cfg.enforcement_mode,
            country_overrides=cfg.country_overrides,
            provably_fair_enabled=cfg.provably_fair_enabled,
            rng_algorithm=cfg.rng_algorithm,
            seed_rotation_interval_rounds=cfg.seed_rotation_interval_rounds,
        )
    else:
        # Default template (config_version_id is null)
        response = CrashMathConfigResponse(
            config_version_id=None,
            schema_version="1.0.0",
            base_rtp=96.0,
            volatility_profile="medium",
            min_multiplier=1.0,
            max_multiplier=500.0,
            max_auto_cashout=100.0,
            round_duration_seconds=12,
            bet_phase_seconds=6,
            grace_period_seconds=2,
            min_bet_per_round=None,
            max_bet_per_round=None,
            max_loss_per_round=None,
            max_win_per_round=None,
            max_rounds_per_session=None,
            max_total_loss_per_session=None,
            max_total_win_per_session=None,
            enforcement_mode="log_only",
            country_overrides={},
            provably_fair_enabled=True,
            rng_algorithm="sha256_chain",
            seed_rotation_interval_rounds=10000,
        )

    logger.info(
        "crash_math_read",
        extra={
            "game_id": game_id,
            "config_version_id": response.config_version_id,
            "core_type": "CRASH",
            "admin_id": "n/a",
            "request_id": request_id,
            "action_type": "crash_math_read",
        },
    )

    return response


@router.post("/{game_id}/config/crash-math", response_model=CrashMathConfig)
async def save_crash_math_config(game_id: str, payload: CrashMathSaveRequest, request: Request):
    from fastapi.responses import JSONResponse

    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    core_type = game_doc.get("core_type") or game_doc.get("coreType")
    if core_type != "CRASH":
        return JSONResponse(
            status_code=404,
            content={
                "error_code": "CRASH_MATH_NOT_AVAILABLE_FOR_GAME",
                "message": "Crash math configuration is only available for CRASH games.",
            },
        )

    admin_id = "current_admin"
    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    # Validation
    if payload.base_rtp < 90 or payload.base_rtp > 99.9:
        return JSONResponse(
            status_code=400,
            content=_crash_math_error(
                "base_rtp must be between 90 and 99.9.",
                "base_rtp",
                payload.base_rtp,
                "out_of_range",
            ),
        )

    if payload.volatility_profile not in {"low", "medium", "high"}:
        return JSONResponse(
            status_code=400,
            content=_crash_math_error(
                "Invalid volatility_profile. Allowed: low, medium, high.",
                "volatility_profile",
                payload.volatility_profile,
                "unsupported_volatility",
            ),
        )

    if payload.min_multiplier < 1.0 or payload.min_multiplier >= payload.max_multiplier:
        return JSONResponse(
            status_code=400,
            content=_crash_math_error(
                "min_multiplier must be >= 1.0 and < max_multiplier.",
                "min_multiplier",
                {
                    "min_multiplier": payload.min_multiplier,
                    "max_multiplier": payload.max_multiplier,
                },
                "invalid_multiplier_range",
            ),
        )

    if payload.max_multiplier > 10000:
        return JSONResponse(
            status_code=400,
            content=_crash_math_error(
                "max_multiplier must be <= 10000.",
                "max_multiplier",
                payload.max_multiplier,
                "too_large",
            ),
        )

    if payload.round_duration_seconds < payload.bet_phase_seconds + payload.grace_period_seconds:
        return JSONResponse(
            status_code=400,
            content=_crash_math_error(
                "round_duration_seconds must be >= bet_phase_seconds + grace_period_seconds.",
                "round_duration_seconds",
                {
                    "round_duration_seconds": payload.round_duration_seconds,
                    "bet_phase_seconds": payload.bet_phase_seconds,
                    "grace_period_seconds": payload.grace_period_seconds,
                },
                "invalid_round_timing",
            ),
        )

    if payload.bet_phase_seconds < 2:
        return JSONResponse(
            status_code=400,
            content=_crash_math_error(
                "bet_phase_seconds must be >= 2.",
                "bet_phase_seconds",
                payload.bet_phase_seconds,
                "too_short",
            ),
        )

    if (
        payload.min_bet_per_round is not None
        and payload.max_bet_per_round is not None
        and payload.min_bet_per_round > payload.max_bet_per_round
    ):
        return JSONResponse(
            status_code=400,
            content=_crash_math_error(
                "min_bet_per_round must be <= max_bet_per_round.",
                "bet_per_round",
                {
                    "min_bet_per_round": payload.min_bet_per_round,
                    "max_bet_per_round": payload.max_bet_per_round,
                },
                "invalid_bet_range",
            ),
        )

    if payload.seed_rotation_interval_rounds is not None and payload.seed_rotation_interval_rounds <= 0:
        return JSONResponse(
            status_code=400,
            content=_crash_math_error(
                "seed_rotation_interval_rounds must be positive when provided.",
                "seed_rotation_interval_rounds",
                payload.seed_rotation_interval_rounds,
                "invalid_seed_rotation_interval",
            ),
        )

    # Normalize enforcement_mode
    normalized_enforcement_mode, err = _validate_enforcement_mode(
        payload.enforcement_mode,
        _crash_math_error,
    )
    if err is not None:
        return err

    # Validate advanced safety limits (simple sanity checks)
    for fname in [
        "max_loss_per_round",
        "max_win_per_round",
        "max_total_loss_per_session",
        "max_total_win_per_session",
    ]:
        _, err = _validate_positive_or_none(fname, getattr(payload, fname), _crash_math_error)
        if err is not None:
            return err

    if payload.max_rounds_per_session is not None and payload.max_rounds_per_session <= 0:
        return JSONResponse(
            status_code=400,
            content=_crash_math_error(
                "max_rounds_per_session must be > 0 when provided.",
                "max_rounds_per_session",
                payload.max_rounds_per_session,
                ValidationReason.MUST_BE_POSITIVE.value,
            ),
        )

    # Country overrides validation
    normalized_country_overrides, err = _validate_country_overrides(
        payload.country_overrides,
        [
            "max_loss_per_round",
            "max_win_per_round",
            "max_rounds_per_session",
            "max_total_loss_per_session",
            "max_total_win_per_session",
        ],
        _crash_math_error,
        parent_field="country_overrides",
    )
    if err is not None:
        return err

    # Fetch previous config for logging
    prev_docs = (
        await db.crash_math_configs
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )
    prev_cfg = CrashMathConfig(**prev_docs[0]) if prev_docs else None

    version = await _generate_new_version(db, game_id, admin_id, notes=payload.summary or "Crash math change")

    cfg = CrashMathConfig(
        game_id=game_id,
        config_version_id=version.id,
        base_rtp=payload.base_rtp,
        volatility_profile=payload.volatility_profile,
        min_multiplier=payload.min_multiplier,
        max_multiplier=payload.max_multiplier,
        max_auto_cashout=payload.max_auto_cashout,
        round_duration_seconds=payload.round_duration_seconds,
        bet_phase_seconds=payload.bet_phase_seconds,
        grace_period_seconds=payload.grace_period_seconds,
        min_bet_per_round=payload.min_bet_per_round,
        max_bet_per_round=payload.max_bet_per_round,
        max_loss_per_round=payload.max_loss_per_round,
        max_win_per_round=payload.max_win_per_round,
        max_rounds_per_session=payload.max_rounds_per_session,
        max_total_loss_per_session=payload.max_total_loss_per_session,
        max_total_win_per_session=payload.max_total_win_per_session,
        enforcement_mode=normalized_enforcement_mode,
        country_overrides=normalized_country_overrides,
        provably_fair_enabled=payload.provably_fair_enabled,
        rng_algorithm=payload.rng_algorithm,
        seed_rotation_interval_rounds=payload.seed_rotation_interval_rounds,
        created_by=admin_id,
    )

    await db.crash_math_configs.insert_one(cfg.model_dump())

    log_details: Dict[str, Any] = {
        "config_version_id": version.id,
        "summary": payload.summary,
        "request_id": request_id,
        "game_id": game_id,
        "core_type": "CRASH",
        "old_value": prev_cfg.model_dump() if prev_cfg else None,
        "new_value": cfg.model_dump(),
    }

    await _append_game_log(db, game_id, admin_id, "crash_math_saved", log_details)

    logger.info(
        "crash_math_saved",
        extra={
            "game_id": game_id,
            "config_version_id": version.id,
            "core_type": "CRASH",
            "admin_id": admin_id,
            "request_id": request_id,
            "action_type": "crash_math_saved",
        },
    )

    return cfg


from fastapi.responses import JSONResponse


def _validate_enforcement_mode(
    value: Optional[str],
    error_builder,
) -> Tuple[Optional[str], Optional[JSONResponse]]:
    """Normalize enforcement_mode or return JSONResponse error.

    Returns (normalized_value, error_response).
    """
    normalized = (value or "log_only").lower()
    if normalized not in {"hard_block", "log_only"}:
        return None, JSONResponse(
            status_code=400,
            content=error_builder(
                "enforcement_mode must be one of: hard_block, log_only.",
                "enforcement_mode",
                normalized,
                ValidationReason.UNSUPPORTED_ENFORCEMENT_MODE.value,
            ),
        )
    return normalized, None


def _validate_positive_or_none(
    field_name: str,
    value: Optional[float],
    error_builder,
) -> Tuple[Optional[float], Optional[JSONResponse]]:
    if value is not None and value <= 0:
        return None, JSONResponse(
            status_code=400,
            content=error_builder(
                f"{field_name} must be > 0 when provided.",
                field_name,
                value,
                ValidationReason.MUST_BE_POSITIVE.value,
            ),
        )
    return value, None


def _validate_country_overrides(
    raw_overrides: Optional[Dict[str, Dict[str, Any]]],
    allowed_keys: List[str],
    error_builder,
    parent_field: str = "country_overrides",
) -> Tuple[Dict[str, Dict[str, Any]], Optional[JSONResponse]]:
    """Shared validation for Crash/Dice country_overrides.

    Returns (normalized_dict, error_response).
    - Ensures ISO 3166-1 alpha-2 country codes
    - Ensures all numeric fields in allowed_keys are > 0 (or positive int for *_rounds / *_bets)
    """
    normalized: Dict[str, Dict[str, Any]] = {}
    if not raw_overrides:
        return normalized, None

    for country_code, overrides in raw_overrides.items():
        if not isinstance(country_code, str) or len(country_code) != 2 or not country_code.isalpha():
            return {}, JSONResponse(
                status_code=400,
                content=error_builder(
                    "country code must be ISO 3166-1 alpha-2 (2 letters).",
                    parent_field,
                    country_code,
                    ValidationReason.INVALID_COUNTRY_CODE.value,
                ),
            )

        upper_code = country_code.upper()
        normalized[upper_code] = dict(overrides) if overrides is not None else {}

        for key in allowed_keys:
            if key in normalized[upper_code] and normalized[upper_code][key] is not None:
                val = normalized[upper_code][key]
                is_int_like = key.endswith("_rounds") or key.endswith("_bets")
                field_path = f"{parent_field}.{upper_code}.{key}"

                if is_int_like:
                    try:
                        int_val = int(val)
                    except (TypeError, ValueError):
                        return {}, JSONResponse(
                            status_code=400,
                            content=error_builder(
                                f"{key} must be a positive integer when provided.",
                                field_path,
                                val,
                                ValidationReason.MUST_BE_POSITIVE.value,
                            ),
                        )
                    if int_val <= 0:
                        return {}, JSONResponse(
                            status_code=400,
                            content=error_builder(
                                f"{key} must be a positive integer when provided.",
                                field_path,
                                val,
                                ValidationReason.MUST_BE_POSITIVE.value,
                            ),
                        )
                    normalized[upper_code][key] = int_val
                else:
                    try:
                        float_val = float(val)
                    except (TypeError, ValueError):
                        return {}, JSONResponse(
                            status_code=400,
                            content=error_builder(
                                f"{key} must be > 0 when provided.",
                                field_path,
                                val,
                                ValidationReason.MUST_BE_POSITIVE.value,
                            ),
                        )
                    if float_val <= 0:
                        return {}, JSONResponse(
                            status_code=400,
                            content=error_builder(
                                f"{key} must be > 0 when provided.",
                                field_path,
                                val,
                                ValidationReason.MUST_BE_POSITIVE.value,
                            ),
                        )
                    normalized[upper_code][key] = float_val

    return normalized, None


# ---------------------------------------------------------------------------
# DICE MATH CONFIG
# ---------------------------------------------------------------------------


def _dice_math_error(message: str, field: str, value: Any = None, reason: str = "invalid") -> Dict[str, Any]:
    details: Dict[str, Any] = {"field": field, "reason": reason}
    if value is not None:
        details["value"] = value
    return {"error_code": "DICE_MATH_VALIDATION_FAILED", "message": message, "details": details}


@router.get("/{game_id}/config/dice-math", response_model=DiceMathConfigResponse)
async def get_dice_math_config(game_id: str, request: Request):
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    core_type = game_doc.get("core_type") or game_doc.get("coreType")
    if core_type != "DICE":
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=404,
            content={
                "error_code": "DICE_MATH_NOT_AVAILABLE_FOR_GAME",
                "message": "Dice math configuration is only available for DICE games.",
            },
        )

    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    docs = (
        await db.dice_math_configs
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )

    if docs:
        cfg = DiceMathConfig(**docs[0])
        response = DiceMathConfigResponse(
            config_version_id=cfg.config_version_id,
            schema_version=cfg.schema_version,
            range_min=cfg.range_min,
            range_max=cfg.range_max,
            step=cfg.step,
            house_edge_percent=cfg.house_edge_percent,
            min_payout_multiplier=cfg.min_payout_multiplier,
            max_payout_multiplier=cfg.max_payout_multiplier,
            allow_over=cfg.allow_over,
            allow_under=cfg.allow_under,
            min_target=cfg.min_target,
            max_target=cfg.max_target,
            round_duration_seconds=cfg.round_duration_seconds,
            bet_phase_seconds=cfg.bet_phase_seconds,
            max_win_per_bet=cfg.max_win_per_bet,
            max_loss_per_bet=cfg.max_loss_per_bet,
            max_session_loss=cfg.max_session_loss,
            max_session_bets=cfg.max_session_bets,
            enforcement_mode=cfg.enforcement_mode,
            country_overrides=cfg.country_overrides,
            provably_fair_enabled=cfg.provably_fair_enabled,
            rng_algorithm=cfg.rng_algorithm,
            seed_rotation_interval_rounds=cfg.seed_rotation_interval_rounds,
        )
    else:
        response = DiceMathConfigResponse(
            config_version_id=None,
            schema_version="1.0.0",
            range_min=0.0,
            range_max=99.99,
            step=0.01,
            house_edge_percent=1.0,
            min_payout_multiplier=1.01,
            max_payout_multiplier=990.0,
            allow_over=True,
            allow_under=True,
            min_target=1.0,
            max_target=98.0,
            round_duration_seconds=5,
            bet_phase_seconds=3,
            max_win_per_bet=None,
            max_loss_per_bet=None,
            max_session_loss=None,
            max_session_bets=None,
            enforcement_mode="log_only",
            country_overrides={},
            provably_fair_enabled=True,
            rng_algorithm="sha256_chain",
            seed_rotation_interval_rounds=20000,
        )

    logger.info(
        "dice_math_read",
        extra={
            "game_id": game_id,
            "config_version_id": response.config_version_id,
            "core_type": "DICE",
            "admin_id": "n/a",
            "request_id": request_id,
            "action_type": "dice_math_read",
        },
    )

    return response


@router.post("/{game_id}/config/dice-math", response_model=DiceMathConfig)
async def save_dice_math_config(game_id: str, payload: DiceMathSaveRequest, request: Request):
    from fastapi.responses import JSONResponse

    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    core_type = game_doc.get("core_type") or game_doc.get("coreType")
    if core_type != "DICE":
        return JSONResponse(
            status_code=404,
            content={
                "error_code": "DICE_MATH_NOT_AVAILABLE_FOR_GAME",
                "message": "Dice math configuration is only available for DICE games.",
            },
        )

    admin_id = "current_admin"
    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    # Validation
    if payload.range_min >= payload.range_max:
        return JSONResponse(
            status_code=400,
            content=_dice_math_error(
                "range_min must be < range_max.",
                "range",
                {"range_min": payload.range_min, "range_max": payload.range_max},
                "invalid_range",
            ),
        )

    if payload.step <= 0:
        return JSONResponse(
            status_code=400,
            content=_dice_math_error(
                "step must be > 0.",
                "step",
                payload.step,
                "invalid_step",
            ),
        )

    steps_count = (payload.range_max - payload.range_min) / payload.step
    if steps_count > 100000:
        return JSONResponse(
            status_code=400,
            content=_dice_math_error(
                "(range_max - range_min) / step must be <= 100000.",
                "step",
                steps_count,
                "too_many_steps",
            ),
        )

    if payload.house_edge_percent <= 0 or payload.house_edge_percent > 5.0:
        return JSONResponse(
            status_code=400,
            content=_dice_math_error(
                "house_edge_percent must be between 0 and 5.",
                "house_edge_percent",
                payload.house_edge_percent,
                "out_of_range",
            ),
        )

    # Advanced limits validation (global)
    for fname in ["max_win_per_bet", "max_loss_per_bet", "max_session_loss"]:
        _, err = _validate_positive_or_none(fname, getattr(payload, fname), _dice_math_error)
        if err is not None:
            return err

    if payload.max_session_bets is not None and payload.max_session_bets <= 0:
        return JSONResponse(
            status_code=400,
            content=_dice_math_error(
                "max_session_bets must be > 0 when provided.",
                "max_session_bets",
                payload.max_session_bets,
                ValidationReason.MUST_BE_POSITIVE.value,
            ),
        )

    # Normalize enforcement_mode
    normalized_enforcement_mode, err = _validate_enforcement_mode(
        payload.enforcement_mode,
        _dice_math_error,
    )
    if err is not None:
        return err

    # Country overrides validation
    normalized_country_overrides, err = _validate_country_overrides(
        payload.country_overrides,
        [
            "max_win_per_bet",
            "max_loss_per_bet",
            "max_session_loss",
            "max_session_bets",
        ],
        _dice_math_error,
        parent_field="country_overrides",
    )
    if err is not None:
        return err

    if payload.min_payout_multiplier < 1.0 or payload.min_payout_multiplier > payload.max_payout_multiplier:
        return JSONResponse(
            status_code=400,
            content=_dice_math_error(
                "min_payout_multiplier must be >= 1.0 and <= max_payout_multiplier.",
                "payout_multiplier",
                {
                    "min_payout_multiplier": payload.min_payout_multiplier,
                    "max_payout_multiplier": payload.max_payout_multiplier,
                },
                "invalid_payout_range",
            ),
        )

    if payload.min_target < payload.range_min or payload.max_target > payload.range_max:
        return JSONResponse(
            status_code=400,
            content=_dice_math_error(
                "min_target and max_target must be within [range_min, range_max].",
                "target_range",
                {
                    "min_target": payload.min_target,
                    "max_target": payload.max_target,
                    "range_min": payload.range_min,
                    "range_max": payload.range_max,
                },
                "invalid_target_range",
            ),
        )

    if payload.round_duration_seconds < payload.bet_phase_seconds:
        return JSONResponse(
            status_code=400,
            content=_dice_math_error(
                "round_duration_seconds must be >= bet_phase_seconds.",
                "round_duration_seconds",
                {
                    "round_duration_seconds": payload.round_duration_seconds,
                    "bet_phase_seconds": payload.bet_phase_seconds,
                },
                "invalid_round_timing",
            ),
        )

    if not (payload.allow_over or payload.allow_under):
        return JSONResponse(
            status_code=400,
            content=_dice_math_error(
                "At least one of allow_over or allow_under must be true.",
                "allow_over_under",
                {"allow_over": payload.allow_over, "allow_under": payload.allow_under},
                "invalid_mode",
            ),
        )

    if payload.seed_rotation_interval_rounds is not None and payload.seed_rotation_interval_rounds <= 0:
        return JSONResponse(
            status_code=400,
            content=_dice_math_error(
                "seed_rotation_interval_rounds must be positive when provided.",
                "seed_rotation_interval_rounds",
                payload.seed_rotation_interval_rounds,
                "invalid_seed_rotation_interval",
            ),
        )

    # Fetch previous config for logging
    prev_docs = (
        await db.dice_math_configs
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )
    prev_cfg = DiceMathConfig(**prev_docs[0]) if prev_docs else None

    version = await _generate_new_version(db, game_id, admin_id, notes=payload.summary or "Dice math change")

    cfg = DiceMathConfig(
        game_id=game_id,
        config_version_id=version.id,
        range_min=payload.range_min,
        range_max=payload.range_max,
        step=payload.step,
        house_edge_percent=payload.house_edge_percent,
        min_payout_multiplier=payload.min_payout_multiplier,
        max_payout_multiplier=payload.max_payout_multiplier,
        allow_over=payload.allow_over,
        allow_under=payload.allow_under,
        min_target=payload.min_target,
        max_target=payload.max_target,
        round_duration_seconds=payload.round_duration_seconds,
        bet_phase_seconds=payload.bet_phase_seconds,
        max_win_per_bet=payload.max_win_per_bet,
        max_loss_per_bet=payload.max_loss_per_bet,
        max_session_loss=payload.max_session_loss,
        max_session_bets=payload.max_session_bets,
        enforcement_mode=normalized_enforcement_mode,
        country_overrides=normalized_country_overrides,
        provably_fair_enabled=payload.provably_fair_enabled,
        rng_algorithm=payload.rng_algorithm,
        seed_rotation_interval_rounds=payload.seed_rotation_interval_rounds,
        created_by=admin_id,
    )

    await db.dice_math_configs.insert_one(cfg.model_dump())

    log_details: Dict[str, Any] = {
        "config_version_id": version.id,
        "summary": payload.summary,
        "request_id": request_id,
        "game_id": game_id,
        "core_type": "DICE",
        "old_value": prev_cfg.model_dump() if prev_cfg else None,
        "new_value": cfg.model_dump(),
    }

    await _append_game_log(db, game_id, admin_id, "dice_math_saved", log_details)

    logger.info(
        "dice_math_saved",
        extra={
            "game_id": game_id,
            "config_version_id": version.id,
            "core_type": "DICE",
            "admin_id": admin_id,
            "request_id": request_id,
            "action_type": "dice_math_saved",
        },
    )

    return cfg


# ---------------------------------------------------------------------------
# SLOT ADVANCED CONFIG
# ---------------------------------------------------------------------------


def _slot_advanced_error(message: str, field: str, value: Any = None, reason: str = "invalid") -> Dict[str, Any]:
    details: Dict[str, Any] = {"field": field, "reason": reason}
    if value is not None:
        details["value"] = value
    return {"error_code": "SLOT_ADVANCED_VALIDATION_FAILED", "message": message, "details": details}


@router.get("/{game_id}/config/slot-advanced", response_model=SlotAdvancedConfigResponse)
async def get_slot_advanced_config(game_id: str, request: Request):
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    core_type = game_doc.get("core_type") or game_doc.get("coreType") or game_doc.get("category")
    if core_type not in {"SLOT", "REEL_LINES", "WAYS", "MEGAWAYS", "slot", "slots", "Slot"}:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=404,
            content={
                "error_code": "SLOT_ADVANCED_NOT_AVAILABLE_FOR_GAME",
                "message": "Slot advanced configuration is only available for slot-type games.",
            },
        )

    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    docs = (
        await db.slot_advanced_configs
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )

    if docs:
        cfg = SlotAdvancedConfig(**docs[0])
        response = SlotAdvancedConfigResponse(
            config_version_id=cfg.config_version_id,
            schema_version=cfg.schema_version,
            spin_speed=cfg.spin_speed,
            turbo_spin_allowed=cfg.turbo_spin_allowed,
            autoplay_enabled=cfg.autoplay_enabled,
            autoplay_default_spins=cfg.autoplay_default_spins,
            autoplay_max_spins=cfg.autoplay_max_spins,
            autoplay_stop_on_big_win=cfg.autoplay_stop_on_big_win,
            autoplay_stop_on_balance_drop_percent=cfg.autoplay_stop_on_balance_drop_percent,
            big_win_animation_enabled=cfg.big_win_animation_enabled,
            gamble_feature_allowed=cfg.gamble_feature_allowed,
        )
    else:
        # Default advanced settings template
        response = SlotAdvancedConfigResponse(
            config_version_id=None,
            schema_version="1.0.0",
            spin_speed="normal",
            turbo_spin_allowed=False,
            autoplay_enabled=True,
            autoplay_default_spins=50,
            autoplay_max_spins=100,
            autoplay_stop_on_big_win=True,
            autoplay_stop_on_balance_drop_percent=None,
            big_win_animation_enabled=True,
            gamble_feature_allowed=False,
        )

    logger.info(
        "slot_advanced_read",
        extra={
            "game_id": game_id,
            "config_version_id": response.config_version_id,
            "core_type": core_type,
            "admin_id": "n/a",
            "request_id": request_id,
            "action_type": "slot_advanced_read",
        },
    )

    return response


@router.post("/{game_id}/config/slot-advanced", response_model=SlotAdvancedConfig)
async def save_slot_advanced_config(game_id: str, payload: SlotAdvancedSaveRequest, request: Request):
    from fastapi.responses import JSONResponse

    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    core_type = game_doc.get("core_type") or game_doc.get("coreType") or game_doc.get("category")
    if core_type not in {"SLOT", "REEL_LINES", "WAYS", "MEGAWAYS", "slot", "slots", "Slot"}:
        return JSONResponse(
            status_code=404,
            content={
                "error_code": "SLOT_ADVANCED_NOT_AVAILABLE_FOR_GAME",
                "message": "Slot advanced configuration is only available for slot-type games.",
            },
        )

    admin_id = "current_admin"
    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    if payload.spin_speed not in {"slow", "normal", "fast"}:
        return JSONResponse(
            status_code=400,
            content=_slot_advanced_error(
                "spin_speed must be one of: slow, normal, fast.",
                "spin_speed",
                payload.spin_speed,
                "unsupported_value",
            ),
        )

    if payload.autoplay_default_spins <= 0 or payload.autoplay_max_spins <= 0:
        return JSONResponse(
            status_code=400,
            content=_slot_advanced_error(
                "autoplay_default_spins and autoplay_max_spins must be > 0.",
                "autoplay_spins",
                {
                    "autoplay_default_spins": payload.autoplay_default_spins,
                    "autoplay_max_spins": payload.autoplay_max_spins,
                },
                "invalid_range",
            ),
        )

    if payload.autoplay_default_spins > payload.autoplay_max_spins:
        return JSONResponse(
            status_code=400,
            content=_slot_advanced_error(
                "autoplay_default_spins must be <= autoplay_max_spins.",
                "autoplay_default_spins",
                {
                    "autoplay_default_spins": payload.autoplay_default_spins,
                    "autoplay_max_spins": payload.autoplay_max_spins,
                },
                "invalid_range",
            ),
        )

    if (
        payload.autoplay_stop_on_balance_drop_percent is not None
        and (payload.autoplay_stop_on_balance_drop_percent <= 0
             or payload.autoplay_stop_on_balance_drop_percent > 100)
    ):
        return JSONResponse(
            status_code=400,
            content=_slot_advanced_error(
                "autoplay_stop_on_balance_drop_percent must be between 0 and 100.",
                "autoplay_stop_on_balance_drop_percent",
                payload.autoplay_stop_on_balance_drop_percent,
                "out_of_range",
            ),
        )

    # Fetch previous config for logging
    prev_docs = (
        await db.slot_advanced_configs
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )
    prev_cfg = SlotAdvancedConfig(**prev_docs[0]) if prev_docs else None

    version = await _generate_new_version(db, game_id, admin_id, notes=payload.summary or "Slot advanced change")

    cfg = SlotAdvancedConfig(
        game_id=game_id,
        config_version_id=version.id,
        spin_speed=payload.spin_speed,
        turbo_spin_allowed=payload.turbo_spin_allowed,
        autoplay_enabled=payload.autoplay_enabled,
        autoplay_default_spins=payload.autoplay_default_spins,
        autoplay_max_spins=payload.autoplay_max_spins,
        autoplay_stop_on_big_win=payload.autoplay_stop_on_big_win,
        autoplay_stop_on_balance_drop_percent=payload.autoplay_stop_on_balance_drop_percent,
        big_win_animation_enabled=payload.big_win_animation_enabled,
        gamble_feature_allowed=payload.gamble_feature_allowed,
        created_by=admin_id,
    )

    await db.slot_advanced_configs.insert_one(cfg.model_dump())

    log_details: Dict[str, Any] = {
        "config_version_id": version.id,
        "summary": payload.summary,
        "request_id": request_id,
        "game_id": game_id,
        "core_type": "SLOT",
        "old_value": prev_cfg.model_dump() if prev_cfg else None,
        "new_value": cfg.model_dump(),
    }

    await _append_game_log(db, game_id, admin_id, "slot_advanced_saved", log_details)

    logger.info(
        "slot_advanced_saved",
        extra={
            "game_id": game_id,
            "config_version_id": version.id,
            "core_type": "SLOT",
            "admin_id": admin_id,
            "request_id": request_id,
            "action_type": "slot_advanced_saved",
        },
    )

    return cfg


# ---------------------------------------------------------------------------
# BLACKJACK RULES CONFIG
# ---------------------------------------------------------------------------


def _blackjack_rules_error(message: str, field: str, value: Any = None, reason: str = "invalid") -> Dict[str, Any]:
    details: Dict[str, Any] = {"field": field, "reason": reason}
    if value is not None:
        details["value"] = value
    return {"error_code": "BLACKJACK_RULES_VALIDATION_FAILED", "message": message, "details": details}


@router.get("/{game_id}/config/blackjack-rules", response_model=BlackjackRulesResponse)
async def get_blackjack_rules(game_id: str, request: Request):
    """Aktif blackjack kurallarını döndür veya default 6-deck S17 3:2 template üretir."""
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    core_type = game_doc.get("core_type") or game_doc.get("coreType")
    if core_type != "TABLE_BLACKJACK":
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=404,
            content={
                "error_code": "BLACKJACK_RULES_NOT_AVAILABLE_FOR_GAME",
                "message": "Blackjack rules configuration is only available for TABLE_BLACKJACK games.",
            },
        )

    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    docs = (
        await db.blackjack_rules
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )

    if docs:
        rules = BlackjackRules(**docs[0])
    else:
        # Default 6-deck, S17, 3:2 payout template (industry standard)
        rules = BlackjackRules(
            game_id=game_id,
            config_version_id=game_doc.get("current_config_version_id") or str(uuid4()),
            deck_count=6,
            dealer_hits_soft_17=False,  # S17: dealer stands on soft 17
            blackjack_payout=1.5,
            double_allowed=True,
            double_after_split_allowed=True,
            split_max_hands=4,
            resplit_aces_allowed=False,
            surrender_allowed=True,
            insurance_allowed=True,
            min_bet=5.0,
            max_bet=500.0,
            side_bets_enabled=False,
            side_bets=None,
            sitout_time_limit_seconds=120,
            disconnect_wait_seconds=30,
            created_by="system_default",
        )

    logger.info(
        "blackjack_rules_read",
        extra={
            "game_id": game_id,
            "config_version_id": rules.config_version_id,
            "core_type": "TABLE_BLACKJACK",
            "admin_id": "n/a",
            "request_id": request_id,
            "action_type": "blackjack_rules_read",
        },
    )

    return BlackjackRulesResponse(rules=rules)


@router.post("/{game_id}/config/blackjack-rules", response_model=BlackjackRules)
async def save_blackjack_rules(game_id: str, payload: BlackjackRulesSaveRequest, request: Request):
    from fastapi.responses import JSONResponse

    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    core_type = game_doc.get("core_type") or game_doc.get("coreType")
    if core_type != "TABLE_BLACKJACK":
        return JSONResponse(
            status_code=404,
            content={
                "error_code": "BLACKJACK_RULES_NOT_AVAILABLE_FOR_GAME",
                "message": "Blackjack rules configuration is only available for TABLE_BLACKJACK games.",
            },
        )

    admin_id = "current_admin"
    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    # Validation - core rules
    if payload.deck_count < 1 or payload.deck_count > 8:
        return JSONResponse(
            status_code=400,
            content=_blackjack_rules_error(
                "deck_count must be between 1 and 8.",
                "deck_count",
                payload.deck_count,
                "out_of_range",
            ),
        )

    if payload.blackjack_payout < 1.2 or payload.blackjack_payout > 1.6:
        return JSONResponse(
            status_code=400,
            content=_blackjack_rules_error(
                "blackjack_payout must be between 1.2 and 1.6 (e.g. 1.5 for 3:2).",
                "blackjack_payout",
                payload.blackjack_payout,
                "out_of_range",
            ),
        )

    if payload.split_max_hands < 1 or payload.split_max_hands > 4:
        return JSONResponse(
            status_code=400,
            content=_blackjack_rules_error(
                "split_max_hands must be between 1 and 4.",
                "split_max_hands",
                payload.split_max_hands,
                "out_of_range",
            ),
        )

    if payload.min_bet <= 0 or payload.min_bet >= payload.max_bet:
        return JSONResponse(
            status_code=400,
            content=_blackjack_rules_error(
                "min_bet must be > 0 and < max_bet.",
                "min_bet",
                {"min_bet": payload.min_bet, "max_bet": payload.max_bet},
                "invalid_limits",
            ),
        )

    # Side bets basic validation
    if payload.side_bets_enabled and payload.side_bets:
        for idx, sb in enumerate(payload.side_bets):
            code = sb.get("code")
            sb_min = sb.get("min_bet")
            sb_max = sb.get("max_bet")
            if not code:
                return JSONResponse(
                    status_code=400,
                    content=_blackjack_rules_error(
                        "Each side bet must have a code.",
                        f"side_bets[{idx}].code",
                        code,
                        "missing",
                    ),
                )
            try:
                sb_min_val = float(sb_min)
                sb_max_val = float(sb_max)
            except Exception:
                return JSONResponse(
                    status_code=400,
                    content=_blackjack_rules_error(
                        "side_bets min_bet and max_bet must be numeric.",
                        f"side_bets[{idx}].min_max",
                        {"min_bet": sb_min, "max_bet": sb_max},
                        "invalid_number",
                    ),
                )
            if sb_min_val <= 0 or sb_min_val >= sb_max_val:
                return JSONResponse(
                    status_code=400,
                    content=_blackjack_rules_error(
                        "side_bets min_bet must be > 0 and < max_bet.",
                        f"side_bets[{idx}].min_max",
                        {"min_bet": sb_min_val, "max_bet": sb_max_val},
                        "invalid_limits",
                    ),
                )
            payout_table = sb.get("payout_table")
            if payout_table is not None and not isinstance(payout_table, dict):
                return JSONResponse(
                    status_code=400,
                    content=_blackjack_rules_error(
                        "side_bets payout_table must be an object when provided.",
                        f"side_bets[{idx}].payout_table",
                        payout_table,
                        "invalid_type",
                    ),
                )

    # Advanced behavior & safety
    if payload.sitout_time_limit_seconds is not None and payload.sitout_time_limit_seconds < 30:
        return JSONResponse(
            status_code=400,
            content=_blackjack_rules_error(
                "sitout_time_limit_seconds must be >= 30.",
                "sitout_time_limit_seconds",
                payload.sitout_time_limit_seconds,
                "too_small",
            ),
        )

    if payload.disconnect_wait_seconds is not None and not (5 <= payload.disconnect_wait_seconds <= 300):
        return JSONResponse(
            status_code=400,
            content=_blackjack_rules_error(
                "disconnect_wait_seconds must be between 5 and 300.",
                "disconnect_wait_seconds",
                payload.disconnect_wait_seconds,
                "out_of_range",
            ),
        )

    if payload.max_same_country_seats is not None and not (1 <= payload.max_same_country_seats <= 10):
        return JSONResponse(
            status_code=400,
            content=_blackjack_rules_error(
                "max_same_country_seats must be between 1 and 10.",
                "max_same_country_seats",
                payload.max_same_country_seats,
                "must_be_between_1_AND_10",
            ),
        )

    if (
        payload.session_max_duration_minutes is not None
        and not (10 <= payload.session_max_duration_minutes <= 1440)
    ):
        return JSONResponse(
            status_code=400,
            content=_blackjack_rules_error(
                "session_max_duration_minutes must be between 10 and 1440.",
                "session_max_duration_minutes",
                payload.session_max_duration_minutes,
                "out_of_range",
            ),
        )

    if payload.max_daily_buyin_limit is not None and payload.max_daily_buyin_limit <= 0:
        return JSONResponse(
            status_code=400,
            content=_blackjack_rules_error(
                "max_daily_buyin_limit must be > 0 when provided.",
                "max_daily_buyin_limit",
                payload.max_daily_buyin_limit,
                "must_be_positive",
            ),
        )

    if payload.table_label is not None and len(payload.table_label) > 50:
        return JSONResponse(
            status_code=400,
            content=_blackjack_rules_error(
                "table_label must be at most 50 characters.",
                "table_label",
                payload.table_label,
                "too_long",
            ),
        )

    if payload.theme is not None and len(payload.theme) > 30:
        return JSONResponse(
            status_code=400,
            content=_blackjack_rules_error(
                "theme must be at most 30 characters.",
                "theme",
                payload.theme,
                "too_long",
            ),
        )

    # Fetch previous for diff logging
    prev_docs = (
        await db.blackjack_rules
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )
    prev_rules = BlackjackRules(**prev_docs[0]) if prev_docs else None

    version = await _generate_new_version(db, game_id, admin_id, notes=payload.summary or "Blackjack rules change")

    rules = BlackjackRules(
        game_id=game_id,
        config_version_id=version.id,
        deck_count=payload.deck_count,
        dealer_hits_soft_17=payload.dealer_hits_soft_17,
        blackjack_payout=payload.blackjack_payout,
        double_allowed=payload.double_allowed,
        double_after_split_allowed=payload.double_after_split_allowed,
        split_max_hands=payload.split_max_hands,
        resplit_aces_allowed=payload.resplit_aces_allowed,
        surrender_allowed=payload.surrender_allowed,
        insurance_allowed=payload.insurance_allowed,
        min_bet=payload.min_bet,
        max_bet=payload.max_bet,
        side_bets_enabled=payload.side_bets_enabled,
        side_bets=payload.side_bets,
        table_label=payload.table_label,
        theme=payload.theme,
        avatar_url=payload.avatar_url,
        banner_url=payload.banner_url,
        auto_seat_enabled=payload.auto_seat_enabled,
        sitout_time_limit_seconds=payload.sitout_time_limit_seconds,
        disconnect_wait_seconds=payload.disconnect_wait_seconds,
        max_same_country_seats=payload.max_same_country_seats,
        block_vpn_flagged_players=payload.block_vpn_flagged_players,
        session_max_duration_minutes=payload.session_max_duration_minutes,
        max_daily_buyin_limit=payload.max_daily_buyin_limit,
        created_by=admin_id,
    )

    await db.blackjack_rules.insert_one(rules.model_dump())

    log_details: Dict[str, Any] = {
        "config_version_id": version.id,
        "summary": payload.summary,
        "request_id": request_id,
        "game_id": game_id,
        "core_type": "TABLE_BLACKJACK",
        "old_value": prev_rules.model_dump() if prev_rules else None,
        "new_value": rules.model_dump(),
    }

    await _append_game_log(db, game_id, admin_id, "blackjack_rules_saved", log_details)

    logger.info(
        "blackjack_rules_saved",
        extra={
            "game_id": game_id,
            "config_version_id": version.id,
            "core_type": "TABLE_BLACKJACK",
            "admin_id": admin_id,
            "request_id": request_id,
            "action_type": "blackjack_rules_saved",
        },
    )

    return rules


# ---------------------------------------------------------------------------
# POKER RULES CONFIG
# ---------------------------------------------------------------------------


def _poker_rules_error(message: str, field: str, value: Any = None, reason: str = "invalid") -> Dict[str, Any]:
    details: Dict[str, Any] = {
        "field": field,
        "reason": reason,
    }
    if value is not None:
        details["value"] = value
    return {
        "error_code": "POKER_RULES_VALIDATION_FAILED",
        "message": message,
        "details": details,
    }


@router.get("/{game_id}/config/poker-rules", response_model=PokerRulesResponse)
async def get_poker_rules(game_id: str, request: Request):
    """Aktif poker kurallarını döndür veya default 6-max NLH template üretir."""
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    core_type = game_doc.get("core_type") or game_doc.get("coreType")
    if core_type != "TABLE_POKER":
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=404,
            content={
                "error_code": "POKER_RULES_NOT_AVAILABLE_FOR_GAME",
                "message": "Poker rules configuration is only available for TABLE_POKER games.",
            },
        )

    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    docs = (
        await db.poker_rules
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )

    if docs:
        rules = PokerRules(**docs[0])
    else:
        # Default 6-max NLH cash table template
        rules = PokerRules(
            game_id=game_id,
            config_version_id=game_doc.get("current_config_version_id") or str(uuid4()),
            variant="texas_holdem",
            limit_type="no_limit",
            min_players=2,
            max_players=6,
            min_buyin_bb=40,
            max_buyin_bb=100,
            rake_type="percentage",
            rake_percent=5.0,
            rake_cap_currency=10.0,
            rake_applies_from_pot=1.0,
            use_antes=False,
            ante_bb=None,
            small_blind_bb=0.5,
            big_blind_bb=1.0,
            allow_straddle=True,
            run_it_twice_allowed=False,
            min_players_to_start=2,
            # Advanced defaults
            sitout_time_limit_seconds=120,
            disconnect_wait_seconds=30,
            created_by="system_default",
        )

    logger.info(
        "poker_rules_read",
        extra={
            "game_id": game_id,
            "config_version_id": rules.config_version_id,
            "core_type": "TABLE_POKER",
            "admin_id": "n/a",
            "request_id": request_id,
            "action_type": "poker_rules_read",
        },
    )

    return PokerRulesResponse(rules=rules)


@router.post("/{game_id}/config/poker-rules", response_model=PokerRules)
async def save_poker_rules(game_id: str, payload: PokerRulesSaveRequest, request: Request):
    from fastapi.responses import JSONResponse

    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    core_type = game_doc.get("core_type") or game_doc.get("coreType")
    if core_type != "TABLE_POKER":
        return JSONResponse(
            status_code=404,
            content={
                "error_code": "POKER_RULES_NOT_AVAILABLE_FOR_GAME",
                "message": "Poker rules configuration is only available for TABLE_POKER games.",
            },
        )

    admin_id = "current_admin"
    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    # Validation - core poker fields
    allowed_variants = {"texas_holdem", "omaha", "omaha_hi_lo", "3card_poker", "caribbean_stud"}
    if payload.variant not in allowed_variants:
        return JSONResponse(
            status_code=400,
            content=_poker_rules_error(
                "Invalid poker variant.",
                "variant",
                payload.variant,
                "unsupported_variant",
            ),
        )

    allowed_limits = {"no_limit", "pot_limit", "fixed_limit"}
    if payload.limit_type not in allowed_limits:
        return JSONResponse(
            status_code=400,
            content=_poker_rules_error(
                "Invalid limit type.",
                "limit_type",
                payload.limit_type,
                "unsupported_limit_type",
            ),
        )

    if payload.min_players < 2 or payload.min_players > payload.max_players or payload.max_players > 10:
        return JSONResponse(
            status_code=400,
            content=_poker_rules_error(
                "min_players and max_players must be between 2 and 10, and min_players <= max_players.",
                "players",
                {"min_players": payload.min_players, "max_players": payload.max_players},
                "invalid_players_range",
            ),
        )

    if payload.min_buyin_bb <= 0 or payload.min_buyin_bb > payload.max_buyin_bb:
        return JSONResponse(
            status_code=400,
            content=_poker_rules_error(
                "min_buyin_bb must be > 0 and <= max_buyin_bb.",
                "buyin_bb",
                {"min_buyin_bb": payload.min_buyin_bb, "max_buyin_bb": payload.max_buyin_bb},
                "invalid_buyin_range",
            ),
        )

    if payload.rake_type == "percentage":
        if payload.rake_percent is None or payload.rake_percent <= 0 or payload.rake_percent > 10:
            return JSONResponse(
                status_code=400,
                content=_poker_rules_error(
                    "rake_percent must be between 0 and 10.",
                    "rake_percent",
                    payload.rake_percent,
                    "out_of_range",
                ),
            )
        if payload.rake_cap_currency is not None and payload.rake_cap_currency < 0:
            return JSONResponse(
                status_code=400,
                content=_poker_rules_error(
                    "rake_cap_currency must be >= 0.",
                    "rake_cap_currency",
                    payload.rake_cap_currency,
                    "negative_cap",
                ),
            )
    elif payload.rake_type == "time":
        # Şimdilik sadece tipe izin veriyoruz, detaylı time rake config bir sonraki fazda eklenecek.
        pass
    elif payload.rake_type == "none":
        pass
    else:
        return JSONResponse(
            status_code=400,
            content=_poker_rules_error(
                "Invalid rake_type. Allowed: percentage, time, none.",
                "rake_type",
                payload.rake_type,
                "unsupported_rake_type",
            ),
        )

    if payload.small_blind_bb <= 0 or payload.big_blind_bb <= payload.small_blind_bb:
        return JSONResponse(
            status_code=400,
            content=_poker_rules_error(
                "small_blind_bb must be > 0 and big_blind_bb must be > small_blind_bb.",
                "blinds",
                {"small_blind_bb": payload.small_blind_bb, "big_blind_bb": payload.big_blind_bb},
                "invalid_blinds",
            ),
        )

    if payload.use_antes and (payload.ante_bb is None or payload.ante_bb <= 0):
        return JSONResponse(
            status_code=400,
            content=_poker_rules_error(
                "ante_bb must be > 0 when use_antes is true.",
                "ante_bb",
                payload.ante_bb,
                "invalid_ante",
            ),
        )

    if payload.min_players_to_start < payload.min_players or payload.min_players_to_start > payload.max_players:
        return JSONResponse(
            status_code=400,
            content=_poker_rules_error(
                "min_players_to_start must be within [min_players, max_players] range.",
                "min_players_to_start",
                payload.min_players_to_start,
                "invalid_min_players_to_start",
            ),
        )

    # Validation - advanced settings
    if payload.auto_rebuy_enabled:
        if payload.auto_rebuy_threshold_bb is None or payload.auto_rebuy_threshold_bb <= 0:
            return JSONResponse(
                status_code=400,
                content=_poker_rules_error(
                    "auto_rebuy_threshold_bb must be > 0 when auto_rebuy_enabled is true.",
                    "auto_rebuy_threshold_bb",
                    payload.auto_rebuy_threshold_bb,
                    "invalid_auto_rebuy_threshold",
                ),
            )

    if payload.sitout_time_limit_seconds is not None and payload.sitout_time_limit_seconds < 30:
        return JSONResponse(
            status_code=400,
            content=_poker_rules_error(
                "sitout_time_limit_seconds must be >= 30.",
                "sitout_time_limit_seconds",
                payload.sitout_time_limit_seconds,
                "too_small",
            ),
        )

    if payload.disconnect_wait_seconds is not None and not (5 <= payload.disconnect_wait_seconds <= 300):
        return JSONResponse(
            status_code=400,
            content=_poker_rules_error(
                "disconnect_wait_seconds must be between 5 and 300.",
                "disconnect_wait_seconds",
                payload.disconnect_wait_seconds,
                "out_of_range",
            ),
        )

    if payload.max_same_country_seats is not None and not (1 <= payload.max_same_country_seats <= 10):
        return JSONResponse(
            status_code=400,
            content=_poker_rules_error(
                "max_same_country_seats must be between 1 and 10.",
                "max_same_country_seats",
                payload.max_same_country_seats,
                "must_be_between_1_and_10",
            ),
        )

    if (
        payload.session_max_duration_minutes is not None
        and not (10 <= payload.session_max_duration_minutes <= 1440)
    ):
        return JSONResponse(
            status_code=400,
            content=_poker_rules_error(
                "session_max_duration_minutes must be between 10 and 1440.",
                "session_max_duration_minutes",
                payload.session_max_duration_minutes,
                "out_of_range",
            ),
        )

    if payload.max_daily_buyin_limit_bb is not None and payload.max_daily_buyin_limit_bb <= 0:
        return JSONResponse(
            status_code=400,
            content=_poker_rules_error(
                "max_daily_buyin_limit_bb must be > 0 when provided.",
                "max_daily_buyin_limit_bb",
                payload.max_daily_buyin_limit_bb,
                "must_be_positive",
            ),
        )

    if payload.table_label is not None and len(payload.table_label) > 50:
        return JSONResponse(
            status_code=400,
            content=_poker_rules_error(
                "table_label must be at most 50 characters.",
                "table_label",
                payload.table_label,
                "too_long",
            ),
        )

    if payload.theme is not None and len(payload.theme) > 30:
        return JSONResponse(
            status_code=400,
            content=_poker_rules_error(
                "theme must be at most 30 characters.",
                "theme",
                payload.theme,
                "too_long",
            ),
        )

    # Fetch previous rules for diff logging
    prev_docs = (
        await db.poker_rules
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )
    prev_rules = PokerRules(**prev_docs[0]) if prev_docs else None

    version = await _generate_new_version(db, game_id, admin_id, notes=payload.summary or "Poker rules change")

    rules = PokerRules(
        game_id=game_id,
        config_version_id=version.id,
        variant=payload.variant,
        limit_type=payload.limit_type,
        min_players=payload.min_players,
        max_players=payload.max_players,
        min_buyin_bb=payload.min_buyin_bb,
        max_buyin_bb=payload.max_buyin_bb,
        rake_type=payload.rake_type,
        rake_percent=payload.rake_percent,
        rake_cap_currency=payload.rake_cap_currency,
        rake_applies_from_pot=payload.rake_applies_from_pot,
        use_antes=payload.use_antes,
        ante_bb=payload.ante_bb,
        small_blind_bb=payload.small_blind_bb,
        big_blind_bb=payload.big_blind_bb,
        allow_straddle=payload.allow_straddle,
        run_it_twice_allowed=payload.run_it_twice_allowed,
        min_players_to_start=payload.min_players_to_start,
        table_label=payload.table_label,
        theme=payload.theme,
        avatar_url=payload.avatar_url,
        banner_url=payload.banner_url,
        auto_muck_enabled=payload.auto_muck_enabled,
        auto_rebuy_enabled=payload.auto_rebuy_enabled,
        auto_rebuy_threshold_bb=payload.auto_rebuy_threshold_bb,
        sitout_time_limit_seconds=payload.sitout_time_limit_seconds,
        disconnect_wait_seconds=payload.disconnect_wait_seconds,
        late_entry_enabled=payload.late_entry_enabled,
        max_same_country_seats=payload.max_same_country_seats,
        block_vpn_flagged_players=payload.block_vpn_flagged_players,
        session_max_duration_minutes=payload.session_max_duration_minutes,
        max_daily_buyin_limit_bb=payload.max_daily_buyin_limit_bb,
        created_by=admin_id,
    )

    await db.poker_rules.insert_one(rules.model_dump())

    # Compute advanced_settings_changed flag
    advanced_fields = [
        "table_label",
        "theme",
        "avatar_url",
        "banner_url",
        "auto_muck_enabled",
        "auto_rebuy_enabled",
        "auto_rebuy_threshold_bb",
        "sitout_time_limit_seconds",
        "disconnect_wait_seconds",
        "late_entry_enabled",
        "max_same_country_seats",
        "block_vpn_flagged_players",
        "session_max_duration_minutes",
        "max_daily_buyin_limit_bb",
    ]

    def _extract_adv(obj: Optional[PokerRules]) -> Optional[Dict[str, Any]]:
        if not obj:
            return None
        return {name: getattr(obj, name) for name in advanced_fields}

    old_adv = _extract_adv(prev_rules)
    new_adv = _extract_adv(rules)
    advanced_changed = old_adv != new_adv

    log_details: Dict[str, Any] = {
        "config_version_id": version.id,
        "summary": payload.summary,
        "request_id": request_id,
        "game_id": game_id,
        "core_type": "TABLE_POKER",
        "old_value": prev_rules.model_dump() if prev_rules else None,
        "new_value": rules.model_dump(),
        "advanced_settings_changed": advanced_changed,
    }

    await _append_game_log(db, game_id, admin_id, "poker_rules_saved", log_details)

    logger.info(
        "poker_rules_saved",
        extra={
            "game_id": game_id,
            "config_version_id": version.id,
            "core_type": "TABLE_POKER",
            "admin_id": admin_id,
            "request_id": request_id,
            "action_type": "poker_rules_saved",
        },
    )

    return rules


# ---------------------------------------------------------------------------
# RTP CONFIG
# ---------------------------------------------------------------------------


class RtpProfileCreate(BaseModel):
    code: str
    rtp_value: float
    is_default: bool = False
    country_overrides: List[RtpCountryOverride] = []


@router.get("/{game_id}/config/rtp", response_model=RtpConfigResponse)
async def get_game_rtp_config(game_id: str):
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    profiles_docs = (
        await db.rtp_profiles
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .to_list(100)
    )
    profiles = [RtpProfile(**p) for p in profiles_docs]

    default_profile_id = game_doc.get("default_rtp_profile_id")
    if not default_profile_id and profiles:
        # pick first marked as default or most recent
        default = next((p for p in profiles if p.is_default), profiles[0])
        default_profile_id = default.id

    return RtpConfigResponse(game_id=game_id, default_profile_id=default_profile_id, profiles=profiles)


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
        details={"rtp_code": profile.code, "rtp_value": profile.rtp_value},
    )
    await db.approvals.insert_one(approval.model_dump())

    await _append_game_log(db, game_id, admin_id, "rtp_profile_created", {"profile_id": profile.id})

    return profile


# ---------------------------------------------------------------------------
# BET CONFIG
# ---------------------------------------------------------------------------


@router.get("/{game_id}/config/bets", response_model=BetConfigResponse)
async def get_bet_config(game_id: str):
    db = get_db()
    cfg_docs = (
        await db.bet_configs
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )
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


# ---------------------------------------------------------------------------
# FEATURE FLAGS
# ---------------------------------------------------------------------------


class GameFeatureFlagsUpdate(GameFeatureFlagsResponse):
    class Config:
        extra = "ignore"


@router.get("/{game_id}/config/features", response_model=GameFeatureFlagsResponse)
async def get_feature_flags(game_id: str):
    db = get_db()
    docs = (
        await db.game_feature_flags
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )
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


@router.post("/{game_id}/config/features", response_model=GameFeatureFlagsResponse)
async def save_feature_flags(game_id: str, payload: GameFeatureFlagsUpdate):
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    admin_id = "current_admin"

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


# ---------------------------------------------------------------------------
# PAYTABLE CONFIG
# ---------------------------------------------------------------------------


class PaytableOverrideRequest(BaseModel):
    data: Dict[str, Any]
    summary: Optional[str] = None


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


def _validate_paytable_payload(data: Dict[str, Any]):
    symbols = data.get("symbols")
    if not isinstance(symbols, list) or not symbols:
        raise PaytableValidationError(_paytable_error("symbols alanı zorunludur.", "data.symbols", "missing"))

    for sym in symbols:
        code = sym.get("code")
        pays = sym.get("pays")
        if not code:
            raise PaytableValidationError(
                _paytable_error("Her sembol için 'code' zorunludur.", "data.symbols[].code", "missing"),
            )
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


@router.post("/{game_id}/config/paytable/override", response_model=PaytableRecord)
async def override_paytable(game_id: str, payload: PaytableOverrideRequest, request: Request):
    from fastapi.responses import JSONResponse

    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    try:
        _validate_paytable_payload(payload.data)
    except PaytableValidationError as exc:
        return JSONResponse(status_code=400, content=exc.payload)

    admin_id = "current_admin"
    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    version = await _generate_new_version(db, game_id, admin_id, notes=payload.summary or "Paytable override")

    record = PaytableRecord(
        game_id=game_id,
        config_version_id=version.id,
        data=payload.data,
        source="override",
        created_by=admin_id,
    )

    doc = record.model_dump()
    if payload.summary:
        doc["summary"] = payload.summary
    await db.paytables.insert_one(doc)

    await _append_game_log(
        db,
        game_id,
        admin_id,
        "paytable_override_saved",
        {
            "config_version_id": version.id,
            "summary": payload.summary,
            "game_id": game_id,
            "admin_id": admin_id,
            "request_id": request_id,
        },
    )

    logger.info(
        "paytable_override_saved",
        extra={
            "game_id": game_id,
            "config_version_id": version.id,
            "admin_id": admin_id,
            "request_id": request_id,
            "action_type": "paytable_override_saved",
        },
    )

    return record


@router.post("/{game_id}/config/paytable/refresh-from-provider")
async def refresh_paytable_from_provider(game_id: str, request: Request):
    """Stub endpoint: creates a provider-based paytable version.

    Gerçek entegrasyon ileride eklenecek. Şimdilik sadece yeni bir versiyon yaratıp loglar.
    """
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    admin_id = "current_admin"
    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    version = await _generate_new_version(db, game_id, admin_id, notes="Paytable refreshed from provider (stub)")

    # Very simple stub: just store empty data with source="provider"
    record = PaytableRecord(
        game_id=game_id,
        config_version_id=version.id,
        data={"symbols": [], "lines": None},
        source="provider",
        created_by=admin_id,
    )

    doc = record.model_dump()
    doc["summary"] = "Provider stub paytable"
    await db.paytables.insert_one(doc)

    await _append_game_log(
        db,
        game_id,
        admin_id,
        "paytable_refreshed_from_provider",
        {
            "config_version_id": version.id,
            "game_id": game_id,
            "admin_id": admin_id,
            "request_id": request_id,
        },
    )

    logger.info(
        "paytable_refreshed_from_provider",
        extra={
            "game_id": game_id,
            "config_version_id": version.id,
            "admin_id": admin_id,
            "request_id": request_id,
            "action_type": "paytable_refreshed_from_provider",
        },
    )

    return {"message": "Paytable refreshed from provider (stub)", "config_version_id": version.id}


# ---------------------------------------------------------------------------
# REEL STRIPS CONFIG
# ---------------------------------------------------------------------------


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


class ReelStripsSaveRequest(BaseModel):
    data: Dict[str, Any]
    source: str = "manual"
    summary: Optional[str] = None


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


# ---------------------------------------------------------------------------
# JACKPOT CONFIG
# ---------------------------------------------------------------------------


class JackpotConfigValidationError(Exception):
    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload


def _jackpot_error(message: str, index: int, field: str, reason: str, value: Any = None) -> Dict[str, Any]:
    details: Dict[str, Any] = {
        "index": index,
        "field": field,
        "reason": reason,
    }
    if value is not None:
        details["value"] = value
    return {
        "error_code": "JACKPOT_CONFIG_VALIDATION_FAILED",
        "message": message,
        "details": details,
    }


def _validate_jackpots(jackpots: List[Dict[str, Any]]):
    if not isinstance(jackpots, list) or not jackpots:
        raise JackpotConfigValidationError(
            _jackpot_error("En az bir jackpot tanımı gereklidir.", -1, "jackpots", "missing"),
        )

    for idx, jp in enumerate(jackpots):
        name = jp.get("name")
        if not isinstance(name, str) or not name.strip():
            raise JackpotConfigValidationError(
                _jackpot_error("Jackpot name boş olamaz.", idx, f"jackpots[{idx}].name", "missing", name),
            )

        currency = jp.get("currency")
        if not isinstance(currency, str) or not currency.strip():
            raise JackpotConfigValidationError(
                _jackpot_error("Currency boş olamaz.", idx, f"jackpots[{idx}].currency", "missing", currency),
            )

        seed = float(jp.get("seed", 0))
        cap = float(jp.get("cap", 0))
        contrib = float(jp.get("contribution_percent", 0))
        hit = float(jp.get("hit_frequency_param", 0))

        if seed < 0:
            raise JackpotConfigValidationError(
                _jackpot_error("Seed 0'dan küçük olamaz.", idx, f"jackpots[{idx}].seed", "negative", seed),
            )
        if cap < seed:
            raise JackpotConfigValidationError(
                _jackpot_error("Cap seed değerinden küçük olamaz.", idx, f"jackpots[{idx}].cap", "cap_lt_seed", cap),
            )
        if contrib < 0 or contrib > 10:
            raise JackpotConfigValidationError(
                _jackpot_error(
                    "Contribution percent 0 ile 10 arasında olmalıdır.",
                    idx,
                    f"jackpots[{idx}].contribution_percent",
                    "out_of_range",
                    contrib,
                ),
            )
        if hit <= 0:
            raise JackpotConfigValidationError(
                _jackpot_error(
                    "hit_frequency_param 0'dan büyük olmalıdır.",
                    idx,
                    f"jackpots[{idx}].hit_frequency_param",
                    "invalid",
                    hit,
                ),
            )


class JackpotConfigSaveRequest(BaseModel):
    jackpots: List[Dict[str, Any]]
    summary: Optional[str] = None


@router.get("/{game_id}/config/jackpots", response_model=JackpotConfigResponse)
async def get_jackpot_config(game_id: str, request: Request):
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    cfg_docs = (
        await db.jackpot_configs
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )
    cfg = JackpotConfig(**cfg_docs[0]) if cfg_docs else None

    # Stub: pools read-only data; in future this should call external jackpot service
    pools_docs = []
    if cfg:
        for jp in cfg.jackpots:
            pools_docs.append(
                JackpotPool(
                    jackpot_name=jp.get("name", "JP"),
                    game_id=game_id,
                    currency=jp.get("currency", "EUR"),
                    current_balance=jp.get("seed", 0.0),
                    last_hit_at=None,
                )
            )

    pools = pools_docs

    if cfg:
        logger.info(
            "jackpot_config_read",
            extra={
                "game_id": game_id,
                "config_version_id": cfg.config_version_id,
                "admin_id": "n/a",
                "request_id": request_id,
                "action_type": "jackpot_config_read",
            },
        )

    return JackpotConfigResponse(config=cfg, pools=pools)


@router.post("/{game_id}/config/jackpots", response_model=JackpotConfig)
async def save_jackpot_config(game_id: str, payload: JackpotConfigSaveRequest, request: Request):
    from fastapi.responses import JSONResponse

    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    # Future lock hook
    if game_doc.get("is_locked_for_math_changes"):
        error_payload = _jackpot_error(
            "Bu oyun için math/jackpot değişiklikleri kilitlidir.",
            -1,
            "game.is_locked_for_math_changes",
            "locked",
        )
        return JSONResponse(status_code=403, content=error_payload)

    try:
        _validate_jackpots(payload.jackpots)
    except JackpotConfigValidationError as exc:
        return JSONResponse(status_code=400, content=exc.payload)

    admin_id = "current_admin"
    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    # Fetch previous config for logging
    prev_cfg_docs = (
        await db.jackpot_configs
        .find({"game_id": game_id}, {"_id": 0})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )

    prev_cfg = JackpotConfig(**prev_cfg_docs[0]) if prev_cfg_docs else None

    version = await _generate_new_version(db, game_id, admin_id, notes="Jackpot config change")

    cfg = JackpotConfig(
        game_id=game_id,
        config_version_id=version.id,
        schema_version="1.0.0",
        jackpots=payload.jackpots,
        created_by=admin_id,
        source="manual",
    )

    await db.jackpot_configs.insert_one(cfg.model_dump())

    details = {
        "old_config_version_id": prev_cfg.config_version_id if prev_cfg else None,
        "new_config_version_id": version.id,
        "summary": payload.summary,
        "game_id": game_id,
        "admin_id": admin_id,
        "request_id": request_id,
        "action_type": "jackpot_config_saved",
    }

    await _append_game_log(db, game_id, admin_id, "jackpot_config_saved", details)

    logger.info(
        "jackpot_config_saved",
        extra={
            "game_id": game_id,
            "config_version_id": version.id,
            "admin_id": admin_id,
            "request_id": request_id,
            "action_type": "jackpot_config_saved",
        },
    )

    # Optional approval hook
    approval = ApprovalRequest(
        category=ApprovalCategory.GAME,
        action_type="jackpot_change",
        related_entity_id=game_id,
        requester_admin=admin_id,
        details={"config_version_id": version.id, "summary": payload.summary},
    )
    await db.approvals.insert_one(approval.model_dump())

    return cfg


# ---------------------------------------------------------------------------
# CONFIG VERSION DIFF (P0-C MVP)
# ---------------------------------------------------------------------------


class ConfigDiffValidationReason(str, Enum):
    TYPE_NOT_SUPPORTED = "type_not_supported"
    VERSION_NOT_FOUND = "version_not_found"
    MISMATCHED_GAME_ID = "mismatched_game_id"


def _config_diff_error(reason: ConfigDiffValidationReason, message: str) -> Dict[str, Any]:
    return {
        "error_code": "CONFIG_DIFF_VALIDATION_FAILED",
        "message": "Config diff parameters are invalid",
        "details": {"reason": reason.value, "message": message},
    }


def _flatten_diff(prefix: str, old: Any, new: Any, changes: List[ConfigDiffChange]):
    """Recursive JSON diff that fills changes list with ConfigDiffChange items.

    prefix: current field path ('' for root), dot-notation with [index] for arrays.
    """

    # Exact equality -> no change
    if old == new:
        return

    # If types are both dict, diff by keys
    if isinstance(old, dict) and isinstance(new, dict):
        all_keys = set(old.keys()) | set(new.keys())
        for key in sorted(all_keys):
            sub_path = f"{prefix}.{key}" if prefix else str(key)
            in_old = key in old
            in_new = key in new
            if in_old and not in_new:
                changes.append(
                    ConfigDiffChange(
                        field_path=sub_path,
                        old_value=old[key],
                        new_value=None,
                        change_type=ConfigDiffChangeType.REMOVED,
                    )
                )
            elif not in_old and in_new:
                changes.append(
                    ConfigDiffChange(
                        field_path=sub_path,
                        old_value=None,
                        new_value=new[key],
                        change_type=ConfigDiffChangeType.ADDED,
                    )
                )
            else:
                _flatten_diff(sub_path, old[key], new[key], changes)
        return

    # If types are both list, diff by index
    if isinstance(old, list) and isinstance(new, list):
        max_len = max(len(old), len(new))
        for idx in range(max_len):
            sub_path = f"{prefix}[{idx}]" if prefix else f"[{idx}]"
            in_old = idx < len(old)
            in_new = idx < len(new)
            if in_old and not in_new:
                changes.append(
                    ConfigDiffChange(
                        field_path=sub_path,
                        old_value=old[idx],
                        new_value=None,
                        change_type=ConfigDiffChangeType.REMOVED,
                    )
                )
            elif not in_old and in_new:
                changes.append(
                    ConfigDiffChange(
                        field_path=sub_path,
                        old_value=None,
                        new_value=new[idx],
                        change_type=ConfigDiffChangeType.ADDED,
                    )
                )
            else:
                _flatten_diff(sub_path, old[idx], new[idx], changes)
        return

    # Primitive or type-changed value: mark as modified
    changes.append(
        ConfigDiffChange(
            field_path=prefix or "",
            old_value=old,
            new_value=new,
            change_type=ConfigDiffChangeType.MODIFIED,
        )
    )


async def _load_config_payload_for_diff(
    db,
    game_id: str,
    config_type: str,
    config_version_id: str,
):
    """Return (payload_dict, error_response) for given config_type/version.

    payload_dict is the JSON subtree we will diff (e.g. SlotAdvancedConfig fields or paytable.data).
    """

    # Slot Advanced
    if config_type == "slot-advanced":
        doc = await db.slot_advanced_configs.find_one(
            {"game_id": game_id, "config_version_id": config_version_id}, {"_id": 0}
        )
        if not doc:
            return None, _config_diff_error(
                ConfigDiffValidationReason.VERSION_NOT_FOUND,
                "Slot advanced config version not found",
            )
        cfg = SlotAdvancedConfig(**doc)
        return (
            {
                "spin_speed": cfg.spin_speed,
                "turbo_spin_allowed": cfg.turbo_spin_allowed,
                "autoplay": {
                    "autoplay_enabled": cfg.autoplay_enabled,
                    "autoplay_default_spins": cfg.autoplay_default_spins,
                    "autoplay_max_spins": cfg.autoplay_max_spins,
                    "autoplay_stop_on_big_win": cfg.autoplay_stop_on_big_win,
                    "autoplay_stop_on_balance_drop_percent": cfg.autoplay_stop_on_balance_drop_percent,
                },
                "big_win_animation_enabled": cfg.big_win_animation_enabled,
                "gamble_feature_allowed": cfg.gamble_feature_allowed,
            },
            None,
        )

    # Paytable
    if config_type == "paytable":
        doc = await db.paytables.find_one(
            {"game_id": game_id, "config_version_id": config_version_id}, {"_id": 0}
        )
        if not doc:
            return None, _config_diff_error(
                ConfigDiffValidationReason.VERSION_NOT_FOUND,
                "Paytable config version not found",
            )
        return doc.get("data") or {}, None

    # Reel strips
    if config_type == "reel-strips":
        doc = await db.reel_strips.find_one(
            {"game_id": game_id, "config_version_id": config_version_id}, {"_id": 0}
        )
        if not doc:
            return None, _config_diff_error(
                ConfigDiffValidationReason.VERSION_NOT_FOUND,
                "Reel strips config version not found",
            )
        return doc.get("data") or {}, None

    # Jackpots
    if config_type == "jackpots":
        doc = await db.jackpot_configs.find_one(
            {"game_id": game_id, "config_version_id": config_version_id}, {"_id": 0}
        )
        if not doc:
            return None, _config_diff_error(
                ConfigDiffValidationReason.VERSION_NOT_FOUND,
                "Jackpot config version not found",
            )
        # For diffing, focus on jackpots array
        return {"jackpots": doc.get("jackpots") or []}, None

    return None, _config_diff_error(
        ConfigDiffValidationReason.TYPE_NOT_SUPPORTED,
        f"Config type '{config_type}' is not supported for diff",
    )


@router.get("/{game_id}/config-diff", response_model=ConfigDiffResponse)
async def get_game_config_diff(
    game_id: str,
    request: Request,
    type: str = Query(..., alias="type"),
    from_config_version_id: str = Query(..., alias="from"),
    to_config_version_id: str = Query(..., alias="to"),
):
    """Compute minimal JSON diff between two config versions for a given game.

    Supported types: slot-advanced, paytable, reel-strips, jackpots.
    """

    db = get_db()

    # Validate game exists
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    # Normalize type
    config_type = type

    # Load both payloads
    old_payload, err = await _load_config_payload_for_diff(
        db, game_id, config_type, from_config_version_id
    )
    if err is not None:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=400, content=err)

    new_payload, err = await _load_config_payload_for_diff(
        db, game_id, config_type, to_config_version_id
    )
    if err is not None:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=400, content=err)

    changes: List[ConfigDiffChange] = []
    _flatten_diff("", old_payload, new_payload, changes)

    return ConfigDiffResponse(
        game_id=game_id,
        config_type=config_type,
        from_config_version_id=from_config_version_id,
        to_config_version_id=to_config_version_id,
        changes=changes,
    )

    version = await _generate_new_version(db, game_id, admin_id, notes="Jackpot config change")

    cfg = JackpotConfig(
        game_id=game_id,
        config_version_id=version.id,
        schema_version="1.0.0",
        jackpots=payload.jackpots,
        created_by=admin_id,
        source="manual",
    )

    await db.jackpot_configs.insert_one(cfg.model_dump())

    details = {
        "old_config_version_id": prev_cfg.config_version_id if prev_cfg else None,
        "new_config_version_id": version.id,
        "summary": payload.summary,
        "game_id": game_id,
        "admin_id": admin_id,
        "request_id": request_id,
        "action_type": "jackpot_config_saved",
    }

    await _append_game_log(db, game_id, admin_id, "jackpot_config_saved", details)

    logger.info(
        "jackpot_config_saved",
        extra={
            "game_id": game_id,
            "config_version_id": version.id,
            "admin_id": admin_id,
            "request_id": request_id,
            "action_type": "jackpot_config_saved",
        },
    )

    # Optional approval hook
    approval = ApprovalRequest(
        category=ApprovalCategory.GAME,
        action_type="jackpot_change",
        related_entity_id=game_id,
        requester_admin=admin_id,
        details={"config_version_id": version.id, "summary": payload.summary},
    )
    await db.approvals.insert_one(approval.model_dump())

    return cfg


# ---------------------------------------------------------------------------
# ASSETS CONFIG
# ---------------------------------------------------------------------------


class AssetUploadError(Exception):
    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload


def _asset_error(message: str, reason: str, details: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "error_code": "ASSET_UPLOAD_FAILED",
        "message": message,
        "details": {"reason": reason, **details},
    }


@router.get("/{game_id}/config/assets", response_model=GameAssetsResponse)
async def get_game_assets(game_id: str, request: Request):
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    docs = (
        await db.game_assets
        .find({"game_id": game_id, "is_deleted": False}, {"_id": 0})
        .sort("created_at", -1)
        .to_list(200)
    )
    assets = [GameAsset(**d) for d in docs]

    logger.info(
        "asset_read",
        extra={
            "game_id": game_id,
            "assets_count": len(assets),
            "admin_id": "n/a",
            "request_id": request_id,
            "action_type": "asset_read",
        },
    )

    return GameAssetsResponse(assets=assets)


from fastapi import UploadFile, File, Form


@router.post("/{game_id}/config/assets/upload", response_model=GameAsset)
async def upload_game_asset(
    game_id: str,
    file: UploadFile = File(...),
    asset_type: str = Form(...),
    language: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    request: Request = None,
):
    from fastapi.responses import JSONResponse

    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    admin_id = "current_admin"
    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    if file is None:
        raise AssetUploadError(_asset_error("File is required.", "missing_file", {}))

    allowed_types = {"logo", "thumbnail", "banner", "background"}
    if asset_type not in allowed_types:
        raise AssetUploadError(
            _asset_error(
                "Invalid asset_type.",
                "invalid_type",
                {"asset_type": asset_type, "allowed_types": sorted(list(allowed_types))},
            )
        )

    mime = file.content_type or "application/octet-stream"
    if not mime.startswith("image/"):
        raise AssetUploadError(
            _asset_error(
                "Only image uploads are supported.",
                "unsupported_mime_type",
                {"mime_type": mime},
            )
        )

    try:
        content = await file.read()
    except Exception:
        raise AssetUploadError(_asset_error("File upload failed.", "read_error", {}))

    size_bytes = len(content)

    version = await _generate_new_version(db, game_id, admin_id, notes="Game asset upload")

    url = f"/static/game-assets/{game_id}/{version.id}/{file.filename}"

    tag_list: List[str] = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    asset = GameAsset(
        game_id=game_id,
        config_version_id=version.id,
        asset_type=asset_type,
        url=url,
        filename=file.filename,
        mime_type=mime,
        size_bytes=size_bytes,
        language=language,
        created_by=admin_id,
        tags=tag_list,
    )

    await db.game_assets.insert_one(asset.model_dump())

    await _append_game_log(
        db,
        game_id,
        admin_id,
        "asset_uploaded",
        {
            "asset_id": asset.id,
            "asset_type": asset.asset_type,
            "config_version_id": version.id,
            "game_id": game_id,
            "admin_id": admin_id,
            "request_id": request_id,
        },
    )

    logger.info(
        "asset_uploaded",
        extra={
            "game_id": game_id,
            "config_version_id": version.id,
            "asset_id": asset.id,
            "admin_id": admin_id,
            "request_id": request_id,
            "action_type": "asset_uploaded",
        },
    )

    return asset


@router.delete("/{game_id}/config/assets/{asset_id}")
async def delete_game_asset(game_id: str, asset_id: str, request: Request):
    db = get_db()
    game_doc = await db.games.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")

    admin_id = "current_admin"
    request_id = request.headers.get("X-Request-ID") or str(uuid4())

    res = await db.game_assets.update_one({"id": asset_id, "game_id": game_id}, {"$set": {"is_deleted": True}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Asset not found")

    await _append_game_log(
        db,
        game_id,
        admin_id,
        "asset_deleted",
        {
            "asset_id": asset_id,
            "game_id": game_id,
            "admin_id": admin_id,
            "request_id": request_id,
        },
    )

    logger.info(
        "asset_deleted",
        extra={
            "game_id": game_id,
            "asset_id": asset_id,
            "admin_id": admin_id,
            "request_id": request_id,
            "action_type": "asset_deleted",
        },
    )

    return {"message": "Asset deleted"}
