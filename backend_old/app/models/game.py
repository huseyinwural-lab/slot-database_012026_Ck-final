from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from enum import Enum


class GameConfigEnvironment(str, Enum):
    PROD = "prod"
    STAGING = "staging"
    SANDBOX = "sandbox"


class GameConfigVersionStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    ROLLED_BACK = "rolled_back"


class GameConfigVersion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    version: str = "1.0.0"
    environment: GameConfigEnvironment = GameConfigEnvironment.PROD
    status: GameConfigVersionStatus = GameConfigVersionStatus.DRAFT
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    published_at: Optional[datetime] = None
    notes: Optional[str] = None


class RtpCountryOverride(BaseModel):
    country: str
    rtp_value: float


class RtpProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    config_version_id: str
    code: str
    rtp_value: float
    is_default: bool = False
    country_overrides: List[RtpCountryOverride] = []
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())


class RtpConfigResponse(BaseModel):
    game_id: str
    default_profile_id: Optional[str] = None
    profiles: List[RtpProfile] = []


class BetCountryOverride(BaseModel):
    country: str
    min_bet: Optional[float] = None
    max_bet: Optional[float] = None


class BetConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    config_version_id: str
    min_bet: float
    max_bet: float
    step: float = 0.1
    presets: List[float] = []
    country_overrides: List[BetCountryOverride] = []
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())


class BetConfigResponse(BaseModel):
    game_id: str
    config: Optional[BetConfig] = None


class GameFeatureFlags(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    config_version_id: str
    features: Dict[str, bool] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())


class GameFeatureFlagsResponse(BaseModel):
    game_id: str
    features: Dict[str, bool] = {}


class GameVisibilityRules(BaseModel):
    countries: List[str] = []
    segments: List[str] = []
    vip_min_level: int = 1


class GameGeneralConfig(BaseModel):
    name: str
    provider: str
    category: str
    default_language: str = "en"
    visibility_rules: GameVisibilityRules = Field(default_factory=GameVisibilityRules)
    lobby_sort_order: int = 0
    tags: List[str] = []
    status: str = "draft"  # active, inactive, maintenance


class GameLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    admin_id: str
    action: str
    details: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())


class GameLogsResponse(BaseModel):
    items: List[GameLog]


class PaytableRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    config_version_id: str
    data: Dict[str, Any]
    source: str  # "provider" or "override"
    schema_version: str = "1.0.0"
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    created_by: str


class PaytableHistoryItem(BaseModel):
    config_version_id: str
    source: str
    created_at: datetime
    created_by: str
    summary: Optional[str] = None


class PaytableResponse(BaseModel):
    current: Optional[PaytableRecord] = None
    history: List[PaytableHistoryItem] = []


class ReelStripsRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    config_version_id: str
    data: Dict[str, Any]
    schema_version: str = "1.0.0"
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    created_by: str
    source: str  # "manual" | "import" | "provider"


class ReelStripsHistoryItem(BaseModel):
    config_version_id: str
    schema_version: str
    source: str
    created_at: datetime
    created_by: str
    summary: Optional[str] = None


class ReelStripsResponse(BaseModel):
    current: Optional[ReelStripsRecord] = None
    history: List[ReelStripsHistoryItem] = []


class JackpotPool(BaseModel):
    jackpot_name: str
    game_id: Optional[str] = None
    currency: str
    current_balance: float
    last_hit_at: Optional[datetime] = None


class JackpotConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    config_version_id: str
    schema_version: str = "1.0.0"
    jackpots: List[Dict[str, Any]]
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    created_by: str
    source: str = "manual"  # "manual" | "import" | "provider"


class GameAsset(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    config_version_id: str
    schema_version: str = "1.0.0"
    asset_type: str  # "logo" | "thumbnail" | "banner" | "background" etc.
    url: str
    filename: str
    mime_type: str
    size_bytes: int
    language: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    created_by: str
    tags: List[str] = []
    is_deleted: bool = False


class GameAssetsResponse(BaseModel):
    assets: List[GameAsset] = []


class JackpotConfigResponse(BaseModel):
    config: Optional[JackpotConfig] = None
    pools: List[JackpotPool] = []


class ConfigDiffChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


class ConfigDiffChange(BaseModel):
    field_path: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    change_type: ConfigDiffChangeType


class ConfigDiffResponse(BaseModel):
    game_id: str
    config_type: str
    from_config_version_id: str
    to_config_version_id: str
    changes: List[ConfigDiffChange] = []



class CrashSafetyCountryOverride(BaseModel):
    max_loss_per_round: Optional[float] = None
    max_win_per_round: Optional[float] = None
    max_rounds_per_session: Optional[int] = None
    max_total_loss_per_session: Optional[float] = None
    max_total_win_per_session: Optional[float] = None


class DiceSafetyCountryOverride(BaseModel):
    max_win_per_bet: Optional[float] = None
    max_loss_per_bet: Optional[float] = None
    max_session_loss: Optional[float] = None
    max_session_bets: Optional[int] = None


class CrashMathConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    config_version_id: str
    schema_version: str = "1.0.0"

    base_rtp: float
    volatility_profile: str  # "low" | "medium" | "high"
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

    # Enforcement behavior for limit breaches
    # Allowed values (API level): "hard_block" | "log_only"
    enforcement_mode: str = "log_only"

    # Country-specific overrides keyed by ISO 3166-1 alpha-2 country code
    country_overrides: Dict[str, CrashSafetyCountryOverride] = {}

    provably_fair_enabled: bool = False
    rng_algorithm: str
    seed_rotation_interval_rounds: Optional[int] = None

    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    created_by: str


class CrashMathConfigResponse(BaseModel):
    config_version_id: Optional[str] = None
    schema_version: str = "1.0.0"
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

    # Advanced safety limits (global)
    max_loss_per_round: Optional[float] = None
    max_win_per_round: Optional[float] = None
    max_rounds_per_session: Optional[int] = None
    max_total_loss_per_session: Optional[float] = None
    max_total_win_per_session: Optional[float] = None

    enforcement_mode: str = "log_only"
    country_overrides: Dict[str, CrashSafetyCountryOverride] = {}

    provably_fair_enabled: bool
    rng_algorithm: str
    seed_rotation_interval_rounds: Optional[int] = None


class DiceMathConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    config_version_id: str
    schema_version: str = "1.0.0"

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

    # Advanced limits (global)
    max_win_per_bet: Optional[float] = None
    max_loss_per_bet: Optional[float] = None
    max_session_loss: Optional[float] = None
    max_session_bets: Optional[int] = None

    # Enforcement behavior for limit breaches
    # Allowed values (API level): "hard_block" | "log_only"
    enforcement_mode: str = "log_only"

    # Country-specific overrides keyed by ISO 3166-1 alpha-2 country code
    country_overrides: Dict[str, DiceSafetyCountryOverride] = {}

    provably_fair_enabled: bool = False
    rng_algorithm: str
    seed_rotation_interval_rounds: Optional[int] = None

    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    created_by: str


class DiceMathConfigResponse(BaseModel):
    config_version_id: Optional[str] = None
    schema_version: str = "1.0.0"
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

    # Advanced limits (global)
    max_win_per_bet: Optional[float] = None
    max_loss_per_bet: Optional[float] = None
    max_session_loss: Optional[float] = None
    max_session_bets: Optional[int] = None

    enforcement_mode: str = "log_only"
    country_overrides: Dict[str, DiceSafetyCountryOverride] = {}

    provably_fair_enabled: bool
    rng_algorithm: str
    seed_rotation_interval_rounds: Optional[int] = None


class PokerRules(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    config_version_id: str
    schema_version: str = "1.0.0"

    # Temel oyun bilgisi
    variant: str  # "texas_holdem", "omaha", "omaha_hi_lo", "3card_poker", "caribbean_stud"
    limit_type: str  # "no_limit", "pot_limit", "fixed_limit"

    min_players: int
    max_players: int

    # Buy-in / stack (BB cinsinden)
    min_buyin_bb: float
    max_buyin_bb: float

    # Rake
    rake_type: str  # "percentage", "time", "none"
    rake_percent: Optional[float] = None
    rake_cap_currency: Optional[float] = None
    rake_applies_from_pot: Optional[float] = None

    # Ante / Blinds
    use_antes: bool = False
    ante_bb: Optional[float] = None
    small_blind_bb: float
    big_blind_bb: float

    # Diğer kurallar
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

    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    created_by: str




class BlackjackRules(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    config_version_id: str
    schema_version: str = "1.0.0"

    # Core rules
    deck_count: int
    dealer_hits_soft_17: bool
    blackjack_payout: float  # 3/2 => 1.5, 6/5 => 1.2
    double_allowed: bool
    double_after_split_allowed: bool
    split_max_hands: int
    resplit_aces_allowed: bool
    surrender_allowed: bool
    insurance_allowed: bool

    # Table limits (currency based)
    min_bet: float
    max_bet: float

    # Side bets
    side_bets_enabled: bool = False
    side_bets: Optional[List[Dict[str, Any]]] = None

    # --- Branding ---
    table_label: Optional[str] = None
    theme: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None

    # --- Behavior ---
    auto_seat_enabled: Optional[bool] = False
    sitout_time_limit_seconds: Optional[int] = 120
    disconnect_wait_seconds: Optional[int] = 30

    # --- Anti-Collusion & Safety ---
    max_same_country_seats: Optional[int] = None
    block_vpn_flagged_players: Optional[bool] = False
    session_max_duration_minutes: Optional[int] = None
    max_daily_buyin_limit: Optional[float] = None

    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    created_by: str


class BlackjackRulesResponse(BaseModel):
    rules: BlackjackRules

class PokerRulesResponse(BaseModel):
    rules: PokerRules


class SlotAdvancedConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    config_version_id: str
    schema_version: str = "1.0.0"

    spin_speed: str = "normal"  # "slow" | "normal" | "fast"
    turbo_spin_allowed: bool = False

    autoplay_enabled: bool = True
    autoplay_default_spins: int = 50
    autoplay_max_spins: int = 100
    autoplay_stop_on_big_win: bool = True
    autoplay_stop_on_balance_drop_percent: Optional[float] = None

    big_win_animation_enabled: bool = True
    gamble_feature_allowed: bool = False

    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    created_by: str


class SlotAdvancedConfigResponse(BaseModel):
    config_version_id: Optional[str] = None
    schema_version: str = "1.0.0"
    spin_speed: str
    turbo_spin_allowed: bool
    autoplay_enabled: bool
    autoplay_default_spins: int
    autoplay_max_spins: int
    autoplay_stop_on_big_win: bool
    autoplay_stop_on_balance_drop_percent: Optional[float] = None
    big_win_animation_enabled: bool
    gamble_feature_allowed: bool
