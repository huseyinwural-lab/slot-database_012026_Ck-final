from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# --- SIMULATION LAB ENUMS ---
class SimulationType(str, Enum):
    GAME_MATH = "game_math"
    PORTFOLIO = "portfolio"
    BONUS = "bonus"
    COHORT_LTV = "cohort_ltv"
    RISK = "risk"
    RG = "rg"
    AB_VARIANT = "ab_variant"
    MIXED = "mixed"

class SimulationStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class GameType(str, Enum):
    SLOTS = "slots"
    BLACKJACK = "blackjack"
    ROULETTE = "roulette"
    BACCARAT = "baccarat"
    CRASH = "crash"
    OTHER = "other"

# --- SIMULATION LAB MODELS ---

class SimulationRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    simulation_type: SimulationType
    status: SimulationStatus = SimulationStatus.DRAFT
    input_snapshot: Dict[str, Any] = {}
    created_by: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    notes: str = ""
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class GameMathSimulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    game_type: GameType
    game_id: Optional[str] = None
    game_name: str
    spins_to_simulate: int = 10000
    seed: Optional[int] = None
    rtp_override: Optional[float] = None
    bet_config: Dict[str, Any] = {}
    results: Dict[str, Any] = {}
    distribution: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class PortfolioSimulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    games: List[Dict[str, Any]] = []
    current_ggr: float = 0.0
    simulated_ggr: float = 0.0
    current_ngr: float = 0.0
    simulated_ngr: float = 0.0
    jackpot_cost: float = 0.0
    bonus_cost: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class BonusSimulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    bonus_template_id: str
    bonus_type: str
    current_percentage: float
    new_percentage: float
    current_wagering: float
    new_wagering: float
    max_win: float
    target_segment: str
    expected_participants: int
    results: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class CohortLTVSimulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    segment_id: str
    segment_name: str
    time_horizon_days: int = 90
    baseline_ltv: float = 0.0
    simulated_ltv: float = 0.0
    deposit_frequency: float = 0.0
    churn_rate: float = 0.0
    bonus_cost: float = 0.0
    rg_flag_rate: float = 0.0
    fraud_risk_impact: float = 0.0
    policy_changes: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class RiskSimulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    risk_rules: List[Dict[str, Any]] = []
    time_window_days: int = 30
    total_alerts_current: int = 0
    total_alerts_simulated: int = 0
    fraud_caught: int = 0
    false_positives: int = 0
    auto_freeze_count: int = 0
    withdrawal_blocks: int = 0
    lost_revenue: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class RGSimulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    current_policy: Dict[str, Any] = {}
    new_policy: Dict[str, Any] = {}
    affected_players: int = 0
    deposits_reduction: float = 0.0
    high_loss_reduced: float = 0.0
    revenue_impact: float = 0.0
    players_hitting_limit_current: int = 0
    players_hitting_limit_simulated: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class ABVariantSimulation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    experiment_id: str
    experiment_name: str
    variants: List[Dict[str, Any]] = []
    player_behaviour_model: Dict[str, Any] = {}
    conversion_uplift: float = 0.0
    revenue_uplift: float = 0.0
    risk_uptick: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class ScenarioBuilder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    scenario_name: str
    scope: List[str] = []
    changes: Dict[str, Any] = {}
    time_horizon_days: int = 30
    target_players: int = 100000
    consolidated_results: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
