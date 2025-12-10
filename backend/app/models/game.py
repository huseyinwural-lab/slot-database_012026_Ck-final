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


class JackpotConfigResponse(BaseModel):
    config: Optional[JackpotConfig] = None
    pools: List[JackpotPool] = []
