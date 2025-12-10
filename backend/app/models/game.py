from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BetConfigResponse(BaseModel):
    game_id: str
    config: Optional[BetConfig] = None


class GameFeatureFlags(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    config_version_id: str
    features: Dict[str, bool] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GameLogsResponse(BaseModel):
    items: List[GameLog]


class PaytableRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    config_version_id: str
    data: Dict[str, Any]
    source: str  # "provider" or "override"
    schema_version: str = "1.0.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str
    tags: List[str] = []
    is_deleted: bool = False


class GameAssetsResponse(BaseModel):
    assets: List[GameAsset] = []


class JackpotConfigResponse(BaseModel):
    config: Optional[JackpotConfig] = None
    pools: List[JackpotPool] = []



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

    provably_fair_enabled: bool = False
    rng_algorithm: str
    seed_rotation_interval_rounds: Optional[int] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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

    provably_fair_enabled: bool = False
    rng_algorithm: str
    seed_rotation_interval_rounds: Optional[int] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str


class PokerRulesResponse(BaseModel):
    rules: PokerRules
