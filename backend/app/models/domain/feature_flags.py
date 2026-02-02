from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# --- FEATURE FLAGS & A/B TESTING ENUMS ---
class FlagStatus(str, Enum):
    ON = "on"
    OFF = "off"
    SCHEDULED = "scheduled"

class FlagType(str, Enum):
    BOOLEAN = "boolean"
    STRING = "string"
    NUMBER = "number"
    JSON = "json"

class FlagScope(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    BOTH = "both"

class Environment(str, Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"

class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"

class MetricType(str, Enum):
    CTR = "ctr"
    CONVERSION = "conversion"
    DEPOSIT = "deposit"
    RETENTION = "retention"
    GAME_REVENUE = "game_revenue"
    SESSION_TIME = "session_time"

# --- FEATURE FLAGS MODELS ---

class FeatureFlag(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    flag_id: str  # user-friendly ID like "new_payment_flow"
    name: str
    description: str
    status: FlagStatus = FlagStatus.OFF
    type: FlagType = FlagType.BOOLEAN
    default_value: Any = False
    scope: FlagScope = FlagScope.BOTH
    environment: Environment = Environment.PRODUCTION
    targeting: Dict[str, Any] = {}  # {rollout_percentage, countries, vip_levels, tags, device}
    group: Optional[str] = None  # "Payments", "Games", "Fraud", etc.
    last_updated_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    scheduled_activation: Optional[datetime] = None

class FlagGroup(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # "Payments", "Games", "Fraud", "CMS", "CRM"
    description: str
    flag_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class Segment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    rules: List[Dict[str, Any]] = []  # [{field, operator, value}]
    population_size: int = 0
    usage_count: int = 0  # how many flags/experiments use this
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class ExperimentVariant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # "A", "B", "C"
    traffic_percentage: float
    value_override: Any = None
    description: Optional[str] = None

class Experiment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    status: ExperimentStatus = ExperimentStatus.DRAFT
    variants: List[ExperimentVariant] = []
    feature_flag_id: Optional[str] = None
    targeting: Dict[str, Any] = {}
    primary_metric: MetricType
    secondary_metrics: List[MetricType] = []
    min_sample_size: int = 1000
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    owner: str
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class ExperimentResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str
    variant_id: str
    variant_name: str
    users_exposed: int = 0
    conversions: int = 0
    conversion_rate: float = 0.0
    revenue: float = 0.0
    deposit_count: int = 0
    statistical_confidence: float = 0.0
    is_winner: bool = False
    metrics: Dict[str, Any] = {}
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class FlagAnalytics(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    flag_id: str
    date: datetime
    activation_rate: float = 0.0
    traffic_distribution: Dict[str, int] = {}
    error_rate: float = 0.0
    conversion_impact: float = 0.0
    player_behavior_changes: Dict[str, Any] = {}

class FlagAuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    admin_name: str
    action: str  # created, updated, deleted, activated, deactivated
    target_type: str  # "flag" or "experiment"
    target_id: str
    target_name: str
    before_value: Optional[Dict[str, Any]] = None
    after_value: Optional[Dict[str, Any]] = None
    ip_address: str
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())

class EnvironmentComparison(BaseModel):
    flag_id: str
    flag_name: str
    production: Dict[str, Any]
    staging: Dict[str, Any]
    differences: List[str] = []
