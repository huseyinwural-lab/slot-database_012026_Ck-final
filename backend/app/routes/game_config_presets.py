from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
from datetime import datetime, timezone
import logging
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient

from config import settings
from app.models.game_config_presets import ConfigPreset
from app.models.game import GameLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/game-config", tags=["game_config_presets"])


def get_db():
  client = AsyncIOMotorClient(settings.mongo_url)
  return client[settings.db_name]


async def _append_game_log(db, game_id: str, admin_id: str, action: str, details: Dict[str, Any]):
  log = GameLog(game_id=game_id, admin_id=admin_id, action=action, details=details)
  await db.game_logs.insert_one(log.model_dump())


async def _ensure_seed_presets(db) -> None:
  """Seed minimum viable preset set if not present.

  Bu fonksiyon production ortamında da idempotent çalışacak şekilde tasarlandı.
  Yalnızca tanımlı id'ler yoksa insert eder.
  """
  seed_presets: List[ConfigPreset] = []

  now = datetime.now(timezone.utc)

  # --- SLOT RTP ---
  seed_presets.append(
    ConfigPreset(
      id="slot_rtp_96_standard",
      game_type="SLOT",
      config_type="rtp",
      name="Slot – 96% RTP Standard",
      description="Standard 96% RTP profile for slots.",
      values={
        "code": "RTP_96",
        "rtp_value": 96.0,
        "is_default": True,
      },
      created_at=now,
      updated_at=now,
    )
  )

  seed_presets.append(
    ConfigPreset(
      id="slot_rtp_94_low",
      game_type="SLOT",
      config_type="rtp",
      name="Slot – 94% RTP Low",
      description="Lower RTP profile (94%) for high-margin markets.",
      values={
        "code": "RTP_94",
        "rtp_value": 94.0,
        "is_default": False,
      },
      created_at=now,
      updated_at=now,
    )
  )

  seed_presets.append(
    ConfigPreset(
      id="slot_rtp_92_aggressive",
      game_type="SLOT",
      config_type="rtp",
      name="Slot – 92% RTP Aggressive",
      description="Lower RTP (92%) aggressive profile for high-volatility slots.",
      values={
        "code": "RTP_92",
        "rtp_value": 92.0,
        "is_default": False,
      },
      created_at=now,
      updated_at=now,
    )
  )


  # --- SLOT BETS ---
  seed_presets.append(
    ConfigPreset(
      id="slot_bets_standard",
      game_type="SLOT",
      config_type="bets",
      name="Slot – Standard Bet Ladder",
      description="Standard bet ladder for slots.",
      values={
        "min_bet": 0.1,
        "max_bet": 100.0,
        "step": 0.1,
        "presets": [0.2, 0.5, 1, 2, 5, 10, 25, 50],
        "country_overrides": [],
      },
      created_at=now,
      updated_at=now,
    )
  )

  # --- CRASH BETS ---
  seed_presets.append(
    ConfigPreset(
      id="crash_bets_standard",
      game_type="CRASH",
      config_type="bets",
      name="Crash – Standard Bet Ladder",
      description="Standard bet ladder for crash games.",
      values={
        "min_bet": 0.5,
        "max_bet": 500.0,
        "step": 0.5,
        "presets": [1, 2, 5, 10, 25, 50, 100],
        "country_overrides": [],
      },
      created_at=now,
      updated_at=now,
    )
  )

  # --- DICE BETS ---
  seed_presets.append(
    ConfigPreset(
      id="dice_bets_standard",
      game_type="DICE",
      config_type="bets",
      name="Dice – Standard Bet Ladder",
      description="Standard bet ladder for dice games.",
      values={
        "min_bet": 0.1,
        "max_bet": 200.0,
        "step": 0.1,
        "presets": [0.5, 1, 2, 5, 10, 25, 50],
        "country_overrides": [],
      },
      created_at=now,
      updated_at=now,
    )
  )

  # --- CRASH ---
  seed_presets.append(
    ConfigPreset(
      id="crash_96_medium",
      game_type="CRASH",
      config_type="crash_math",
      name="Crash – 96% Medium Volatility",
      description="Standard medium volatility crash configuration with 96% target RTP.",
      values={
        "base_rtp": 96.0,
        "volatility_profile": "medium",
        "min_multiplier": 1.0,
        "max_multiplier": 500.0,
        "max_auto_cashout": 200.0,
        "round_duration_seconds": 12,
        "bet_phase_seconds": 6,
        "grace_period_seconds": 2,
        "min_bet_per_round": None,
        "max_bet_per_round": None,
        "provably_fair_enabled": True,
        "rng_algorithm": "sha256_chain",
        "seed_rotation_interval_rounds": 10000,
        "summary": "Crash 96% RTP medium volatility preset.",
      },
      created_at=now,
      updated_at=now,
    )
  )

  seed_presets.append(
    ConfigPreset(
      id="crash_97_high",
      game_type="CRASH",
      config_type="crash_math",
      name="Crash – 97% High Volatility Turbo",
      description="Higher RTP and higher max multiplier for aggressive crash profile.",
      values={
        "base_rtp": 97.0,
        "volatility_profile": "high",
        "min_multiplier": 1.0,
        "max_multiplier": 1000.0,
        "max_auto_cashout": 500.0,
        "round_duration_seconds": 14,
        "bet_phase_seconds": 7,
        "grace_period_seconds": 2,
        "min_bet_per_round": None,
        "max_bet_per_round": None,
        "provably_fair_enabled": True,
        "rng_algorithm": "sha256_chain",
        "seed_rotation_interval_rounds": 8000,
        "summary": "Crash 97% RTP high volatility turbo preset.",
      },
      created_at=now,
      updated_at=now,
    )
  )

  # --- DICE ---
  seed_presets.append(
    ConfigPreset(
      id="dice_standard_1percent",
      game_type="DICE",
      config_type="dice_math",
      name="Dice – 1% House Edge Standard",
      description="Standard dice config with 1% house edge and full over/under.",
      values={
        "range_min": 0.0,
        "range_max": 99.99,
        "step": 0.01,
        "house_edge_percent": 1.0,
        "min_payout_multiplier": 1.01,
        "max_payout_multiplier": 990.0,
        "allow_over": True,
        "allow_under": True,
        "min_target": 1.0,
        "max_target": 98.0,
        "round_duration_seconds": 5,
        "bet_phase_seconds": 3,
        "provably_fair_enabled": True,
        "rng_algorithm": "sha256_chain",
        "seed_rotation_interval_rounds": 20000,
        "summary": "Standard 1% house edge dice config.",
      },
      created_at=now,
      updated_at=now,
    )
  )

  seed_presets.append(
    ConfigPreset(
      id="dice_over_only_low_risk",
      game_type="DICE",
      config_type="dice_math",
      name="Dice – Over-Only Low Risk",
      description="Lower variance dice profile allowing only over bets in safer target band.",
      values={
        "range_min": 0.0,
        "range_max": 99.99,
        "step": 0.01,
        "house_edge_percent": 1.5,
        "min_payout_multiplier": 1.01,
        "max_payout_multiplier": 100.0,
        "allow_over": True,
        "allow_under": False,
        "min_target": 50.0,
        "max_target": 95.0,
        "round_duration_seconds": 5,
        "bet_phase_seconds": 3,
        "provably_fair_enabled": True,
        "rng_algorithm": "sha256_chain",
        "seed_rotation_interval_rounds": 15000,
        "summary": "Over-only low risk dice config.",
      },
      created_at=now,
      updated_at=now,
    )
  )

  seed_presets.append(
    ConfigPreset(
      id="dice_under_only_high_risk",
      game_type="DICE",
      config_type="dice_math",
      name="Dice – Under-Only High Risk",
      description="High risk dice profile allowing only under bets near low edge of range.",
      values={
        "range_min": 0.0,
        "range_max": 99.99,
        "step": 0.01,
        "house_edge_percent": 2.0,
        "min_payout_multiplier": 2.0,
        "max_payout_multiplier": 990.0,
        "allow_over": False,
        "allow_under": True,
        "min_target": 1.0,
        "max_target": 20.0,
        "round_duration_seconds": 5,
        "bet_phase_seconds": 3,
        "provably_fair_enabled": True,
        "rng_algorithm": "sha256_chain",
        "seed_rotation_interval_rounds": 25000,
        "summary": "Under-only high risk dice config.",
      },
      created_at=now,
      updated_at=now,
    )
  )

  # --- BLACKJACK ---
  seed_presets.append(
    ConfigPreset(
      id="bj_european_s17_3to2_standard",
      game_type="TABLE_BLACKJACK",
      config_type="blackjack_rules",
      name="Blackjack – European S17 3:2 Standard",
      description="Standard 6-deck S17 3:2 blackjack table without side bets.",
      values={
        "deck_count": 6,
        "dealer_hits_soft_17": False,
        "blackjack_payout": 1.5,
        "double_allowed": True,
        "double_after_split_allowed": True,
        "split_max_hands": 4,
        "resplit_aces_allowed": False,
        "surrender_allowed": True,
        "insurance_allowed": True,
        "min_bet": 5.0,
        "max_bet": 500.0,
        "side_bets_enabled": False,
        "side_bets": None,
        "table_label": "BJ European S17 Standard",
        "theme": "bj_standard",
        "auto_seat_enabled": True,
        "sitout_time_limit_seconds": 120,
        "disconnect_wait_seconds": 30,
        "max_same_country_seats": None,
        "block_vpn_flagged_players": False,
        "session_max_duration_minutes": None,
        "max_daily_buyin_limit": None,
      },
      created_at=now,
      updated_at=now,
    )
  )

  seed_presets.append(
    ConfigPreset(
      id="bj_vegas_h17_3to2_sidebets_enabled",
      game_type="TABLE_BLACKJACK",
      config_type="blackjack_rules",
      name="Blackjack – Vegas H17 3:2 + Side Bets",
      description="Vegas style H17 3:2 blackjack table with popular side bets.",
      values={
        "deck_count": 6,
        "dealer_hits_soft_17": True,
        "blackjack_payout": 1.5,
        "double_allowed": True,
        "double_after_split_allowed": True,
        "split_max_hands": 4,
        "resplit_aces_allowed": False,
        "surrender_allowed": True,
        "insurance_allowed": True,
        "min_bet": 10.0,
        "max_bet": 1000.0,
        "side_bets_enabled": True,
        "side_bets": [
          {
            "code": "perfect_pairs",
            "min_bet": 2.0,
            "max_bet": 50.0,
            "payout_table": {"mixed": 5, "colored": 10, "perfect": 25},
          },
          {
            "code": "21_3",
            "min_bet": 2.0,
            "max_bet": 50.0,
            "payout_table": {"flush": 5, "straight": 10, "three_of_a_kind": 30},
          },
        ],
        "table_label": "BJ Vegas H17 VIP",
        "theme": "bj_vegas_vip",
        "auto_seat_enabled": True,
        "sitout_time_limit_seconds": 120,
        "disconnect_wait_seconds": 45,
        "max_same_country_seats": 2,
        "block_vpn_flagged_players": True,
        "session_max_duration_minutes": 240,
        "max_daily_buyin_limit": 5000.0,
      },
      created_at=now,
      updated_at=now,
    )
  )

  seed_presets.append(
    ConfigPreset(
      id="bj_lowstakes_beginner_friendly",
      game_type="TABLE_BLACKJACK",
      config_type="blackjack_rules",
      name="Blackjack – Lowstakes Beginner Friendly",
      description="Low minimum bet, beginner friendly blackjack configuration.",
      values={
        "deck_count": 4,
        "dealer_hits_soft_17": False,
        "blackjack_payout": 1.5,
        "double_allowed": True,
        "double_after_split_allowed": False,
        "split_max_hands": 3,
        "resplit_aces_allowed": False,
        "surrender_allowed": False,
        "insurance_allowed": True,
        "min_bet": 1.0,
        "max_bet": 50.0,
        "side_bets_enabled": False,
        "side_bets": None,
        "table_label": "BJ Lowstakes Beginner",
        "theme": "bj_beginner",
        "auto_seat_enabled": False,
        "sitout_time_limit_seconds": 180,
        "disconnect_wait_seconds": 60,
        "max_same_country_seats": None,
        "block_vpn_flagged_players": False,
        "session_max_duration_minutes": 120,
        "max_daily_buyin_limit": 500.0,
      },
      created_at=now,
      updated_at=now,
    )
  )


  # --- POKER ---
  seed_presets.append(
    ConfigPreset(
      id="poker_6max_nlh_eu",
      game_type="TABLE_POKER",
      config_type="poker_rules",
      name="Poker – 6-max NLH EU Standard",
      description="6-max No Limit Hold'em cash table with standard EU rake.",
      values={
        "variant": "texas_holdem",
        "limit_type": "no_limit",
        "min_players": 2,
        "max_players": 6,
        "min_buyin_bb": 40,
        "max_buyin_bb": 100,
        "rake_type": "percentage",
        "rake_percent": 5.0,
        "rake_cap_currency": 8.0,
        "rake_applies_from_pot": 1.0,
        "use_antes": False,
        "ante_bb": None,
        "small_blind_bb": 0.5,
        "big_blind_bb": 1.0,
        "allow_straddle": True,
        "run_it_twice_allowed": False,
        "min_players_to_start": 2,
        "summary": "6-max NLH EU standard rake preset.",
      },
      created_at=now,
      updated_at=now,
    )
  )

  seed_presets.append(
    ConfigPreset(
      id="poker_9max_nlh_classic",
      game_type="TABLE_POKER",
      config_type="poker_rules",
      name="Poker – 9-max NLH Classic",
      description="Full ring No Limit Hold'em cash table.",
      values={
        "variant": "texas_holdem",
        "limit_type": "no_limit",
        "min_players": 2,
        "max_players": 9,
        "min_buyin_bb": 20,
        "max_buyin_bb": 100,
        "rake_type": "percentage",
        "rake_percent": 5.0,
        "rake_cap_currency": 10.0,
        "rake_applies_from_pot": 1.0,
        "use_antes": False,
        "ante_bb": None,
        "small_blind_bb": 0.5,
        "big_blind_bb": 1.0,
        "allow_straddle": False,
        "run_it_twice_allowed": False,
        "min_players_to_start": 3,
        "summary": "9-max NLH classic rake preset.",
      },
      created_at=now,
      updated_at=now,
    )
  )

  seed_presets.append(
    ConfigPreset(
      id="poker_omaha_potlimit_default",
      game_type="TABLE_POKER",
      config_type="poker_rules",
      name="Poker – Omaha Pot Limit Default",
      description="Standard 6-max Pot Limit Omaha cash table.",
      values={
        "variant": "omaha",
        "limit_type": "pot_limit",
        "min_players": 2,
        "max_players": 6,
        "min_buyin_bb": 40,
        "max_buyin_bb": 100,
        "rake_type": "percentage",
        "rake_percent": 5.0,
        "rake_cap_currency": 8.0,
        "rake_applies_from_pot": 1.0,
        "use_antes": False,
        "ante_bb": None,
        "small_blind_bb": 0.5,
        "big_blind_bb": 1.0,
        "allow_straddle": True,
        "run_it_twice_allowed": False,
        "min_players_to_start": 2,
        "summary": "Omaha PLO default cash table preset.",
      },
      created_at=now,
      updated_at=now,
    )
  )

  # Insert if missing
  for preset in seed_presets:
    exists = await db.config_presets.find_one({"id": preset.id}, {"_id": 0})
    if not exists:
      await db.config_presets.insert_one(preset.model_dump())


@router.get("/presets")
async def list_presets(game_type: str, config_type: str):
  """Listele: belirli game_type + config_type için preset başlıkları."""
  db = get_db()
  await _ensure_seed_presets(db)

  cursor = db.config_presets.find(
    {"game_type": game_type, "config_type": config_type}, {"_id": 0, "id": 1, "name": 1}
  ).sort("name", 1)
  presets = await cursor.to_list(100)

  return {"presets": presets}


@router.get("/presets/{preset_id}")
async def get_preset(preset_id: str):
  db = get_db()
  await _ensure_seed_presets(db)

  doc = await db.config_presets.find_one({"id": preset_id}, {"_id": 0})
  if not doc:
    return JSONResponse(
      status_code=404,
      content={
        "error_code": "PRESET_NOT_FOUND",
        "message": f"Preset {preset_id} not found.",
      },
    )

  return doc


@router.post("/presets/{preset_id}/apply")
async def apply_preset(preset_id: str, payload: Dict[str, Any], request: Request):
  """Sadece preset uygulama log'u yazar. Config'i değiştirmez/versiyon yaratmaz."""
  db = get_db()

  doc = await db.config_presets.find_one({"id": preset_id}, {"_id": 0})
  if not doc:
    return JSONResponse(
      status_code=404,
      content={
        "error_code": "PRESET_NOT_FOUND",
        "message": f"Preset {preset_id} not found.",
      },
    )

  game_id = payload.get("game_id")
  game_type = payload.get("game_type")
  config_type = payload.get("config_type")

  if not game_id or not game_type or not config_type:
    return JSONResponse(
      status_code=400,
      content={
        "error_code": "PRESET_APPLY_INVALID_PAYLOAD",
        "message": "game_id, game_type and config_type are required.",
      },
    )

  admin_id = "current_admin"  # TODO: real auth integration
  request_id = request.headers.get("X-Request-ID") or str(uuid4())

  await _append_game_log(
    db,
    game_id,
    admin_id,
    "preset_applied",
    {
      "preset_id": preset_id,
      "preset_game_type": doc.get("game_type"),
      "preset_config_type": doc.get("config_type"),
      "applied_game_type": game_type,
      "config_type": config_type,
      "request_id": request_id,
    },
  )

  logger.info(
    "preset_applied",
    extra={
      "game_id": game_id,
      "preset_id": preset_id,
      "game_type": game_type,
      "config_type": config_type,
      "request_id": request_id,
    },
  )

  return {"message": "Preset apply logged."}
