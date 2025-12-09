from fastapi import APIRouter, HTTPException, Body, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

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
)

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
