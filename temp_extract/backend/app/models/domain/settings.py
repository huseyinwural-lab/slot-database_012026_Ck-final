from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# --- SETTINGS PANEL / MULTI-TENANT ENUMS ---
class BrandStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"

class MaintenanceType(str, Enum):
    FULL = "full"
    GAMES = "games"
    PAYMENTS = "payments"
    PARTIAL = "partial"

class ConfigEnvironment(str, Enum):
    STAGING = "staging"
    PRODUCTION = "production"
    QA = "qa"

class ConfigStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    LIVE = "live"
    ROLLED_BACK = "rolled_back"

# --- SETTINGS PANEL MODELS ---

class Brand(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brand_name: str
    status: BrandStatus = BrandStatus.ACTIVE
    default_currency: str = "USD"
    default_language: str = "en"
    domains: List[str] = []
    languages_supported: List[str] = ["en"]
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    contact_info: Dict[str, Any] = {}
    timezone: str = "UTC"
    country_availability: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class DomainMarket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain: str
    brand_id: str
    market: str  # TR, EU, LATAM, CA
    status: str = "active"
    geo_targeting_rules: Dict[str, Any] = {}
    currency: str = "USD"
    payment_methods: List[str] = []
    rg_ruleset: str = "default"
    regulatory_class: str = "standard"
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class Currency(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    currency_code: str
    symbol: str
    exchange_rate: float = 1.0
    base_currency: str = "USD"
    update_method: str = "manual"  # manual or API
    rounding_rules: Dict[str, Any] = {}
    min_deposit: float = 10.0
    max_deposit: float = 10000.0
    min_bet: float = 0.1
    max_bet: float = 1000.0
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class PaymentProvider(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_name: str
    brand_id: str
    provider_type: str  # deposit or withdrawal
    api_keys: Dict[str, str] = {}  # masked
    status: str = "active"
    availability_countries: List[str] = []
    min_amount: float = 10.0
    max_amount: float = 10000.0
    fees: Dict[str, Any] = {}
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class CountryRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    country_code: str
    country_name: str
    is_allowed: bool = True
    games_allowed: bool = True
    bonuses_allowed: bool = True
    kyc_level: int = 1
    payment_restrictions: List[str] = []
    default_language: str = "en"
    regulatory_notes: str = ""
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class GameAvailabilityRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    brand_id: str
    country_code: str
    is_allowed: bool = True
    rtp_override_allowed: bool = False
    provider_restrictions: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class CommunicationProvider(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_name: str
    provider_type: str  # email, sms, push
    api_keys: Dict[str, str] = {}
    from_name: Optional[str] = None
    from_number: Optional[str] = None
    rate_limits: Dict[str, int] = {}
    country_restrictions: List[str] = []
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class RegulatorySettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    jurisdiction: str
    age_verification_required: bool = True
    min_age: int = 18
    kyc_tiers: List[Dict[str, Any]] = []
    self_exclusion_rules: Dict[str, Any] = {}
    betting_limits: Dict[str, Any] = {}
    min_rtp_requirement: float = 85.0
    aml_threshold: float = 10000.0
    pep_check_required: bool = True
    rg_messages: Dict[str, str] = {}
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class PlatformDefaults(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    default_language: str = "en"
    default_currency: str = "USD"
    default_timezone: str = "UTC"
    session_timeout_minutes: int = 30
    password_min_length: int = 8
    require_2fa: bool = False
    cache_ttl_seconds: int = 300
    pagination_default: int = 20
    api_rate_limit_per_minute: int = 60
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())


class NewMemberManualBonusConfig(BaseModel):
    enabled: bool = False
    allowed_game_ids: List[str] = []
    spin_count: int = 0
    fixed_bet_amount: float = 0.0
    total_budget_cap: float = 0.0
    validity_days: int = 7

class APIKey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key_name: str
    key_hash: str  # hashed API key
    owner: str  # brand_id or "system"
    permissions: List[str] = []
    last_used: Optional[datetime] = None
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class Webhook(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    endpoint_url: str
    secret_token: str
    retry_policy: Dict[str, Any] = {"max_retries": 3, "backoff": "exponential"}
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class ThemeBranding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brand_id: str
    logo_url: Optional[str] = None
    color_palette: Dict[str, str] = {}
    typography: Dict[str, str] = {}
    background_images: List[str] = []
    email_templates: Dict[str, str] = {}
    custom_css: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class MaintenanceSchedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brand_id: str
    maintenance_type: MaintenanceType
    start_time: datetime
    end_time: datetime
    message: Dict[str, str] = {}  # multilingual
    affecting: List[str] = ["entire_site"]
    status: str = "scheduled"
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class ConfigVersion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version_number: str
    created_by: str
    environment: ConfigEnvironment
    change_summary: str
    config_snapshot: Dict[str, Any] = {}
    status: ConfigStatus = ConfigStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    deployed_at: Optional[datetime] = None

class ConfigAuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    admin_name: str
    action: str
    module: str
    before_value: Optional[Dict[str, Any]] = None
    after_value: Optional[Dict[str, Any]] = None
    ip_address: str
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
