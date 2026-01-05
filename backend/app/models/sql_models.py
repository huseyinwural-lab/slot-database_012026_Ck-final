from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, Text
from sqlalchemy.dialects.postgresql import JSONB
import uuid

if TYPE_CHECKING:
    from app.models.game_models import Game

# --- SHARED MODELS ---

class Tenant(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True, unique=True)
    type: str = "renter"  # owner | renter
    features: Dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    # Per-tenant payment policy (TENANT-POLICY-001)
    daily_deposit_limit: Optional[float] = None
    daily_withdraw_limit: Optional[float] = None
    payout_retry_limit: Optional[int] = None
    payout_cooldown_seconds: Optional[int] = None

    admins: List["AdminUser"] = Relationship(back_populates="tenant")
    players: List["Player"] = Relationship(back_populates="tenant")
    games: List["Game"] = Relationship(back_populates="tenant")
    tickets: List["SupportTicket"] = Relationship(back_populates="tenant")
    bonuses: List["Bonus"] = Relationship(back_populates="tenant")


class AdminUser(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    username: str
    email: str = Field(unique=True, index=True)
    full_name: str
    password_hash: str
    role: str 
    tenant_role: Optional[str] = "tenant_admin"
    is_platform_owner: bool = False
    status: str = "active"
    is_active: bool = True
    mfa_enabled: bool = False # P0-CUTOVER-02
    failed_login_attempts: int = 0
    invite_token: Optional[str] = None
    password_reset_token: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    tenant: Tenant = Relationship(back_populates="admins")


class Player(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    username: str = Field(index=True)
    email: str = Field(index=True)
    password_hash: str
    # Legacy aggregate balance fields (kept for backward compatibility)
    balance_real: float = 0.0
    balance_bonus: float = 0.0
    # New split balances for prod-grade wallet
    # Bonus Wagering (Sprint B)
    wagering_requirement: float = 0.0
    wagering_remaining: float = 0.0
    balance_real_available: float = 0.0
    balance_real_held: float = 0.0
    status: str = "active"
    kyc_status: str = "pending"
    risk_score: str = "low"
    last_login: Optional[datetime] = None
    registered_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    tenant: Tenant = Relationship(back_populates="players")
    transactions: List["Transaction"] = Relationship(back_populates="player")
    tickets: List["SupportTicket"] = Relationship(back_populates="player")


class Transaction(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    player_id: str = Field(foreign_key="player.id", index=True)
    type: str 
    amount: float
    currency: str = "USD"
    status: str 
    # New state machine field (created/pending_provider/completed/failed/reversed, requested/under_review/approved/paid/rejected/canceled)
    state: str = "created"
    method: Optional[str] = None
    provider_tx_id: Optional[str] = None
    # Idempotency and provider event identifiers
    idempotency_key: Optional[str] = None
    provider: Optional[str] = None
    provider_event_id: Optional[str] = None
    # Review / manual intervention metadata
    review_reason: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    # Extra metadata (e.g. webhook payload hashes)
    metadata_json: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column("metadata", JSON().with_variant(JSONB, "postgresql")),
    )
    balance_after: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    player: Player = Relationship(back_populates="transactions")


# --- NEW MODELS FOR FULL COVERAGE ---

class TicketMessage(SQLModel): 
    sender: str
    text: str
    timestamp: str

class SupportTicket(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    player_id: str = Field(foreign_key="player.id", index=True)
    subject: str
    status: str = "open" # open, answered, closed
    priority: str = "medium"
    messages: List[Dict] = Field(default=[], sa_column=Column(JSON)) # List of {sender, text, time}
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    tenant: Tenant = Relationship(back_populates="tickets")
    player: Player = Relationship(back_populates="tickets")


class Bonus(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    name: str
    type: str # deposit_match, freespin
    rules: Dict = Field(default={}, sa_column=Column(JSON))
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    tenant: Tenant = Relationship(back_populates="bonuses")


class AuditLog(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    admin_id: str
    action: str
    module: str
    target_id: Optional[str] = None
    details: Dict = Field(default={}, sa_column=Column(JSON))
    ip_address: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())




class AuditEvent(SQLModel, table=True):
    """Canonical audit trail for critical admin actions (P2).

    Required fields:
    - request_id, actor_user_id, tenant_id, action, resource_type, resource_id, result
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

    # Correlation
    request_id: str = Field(index=True)

    # Actor
    actor_user_id: str = Field(index=True)
    actor_role: Optional[str] = None # Added Task 4

    # Tenant scope
    tenant_id: str = Field(index=True)

    # Event classification
    action: str = Field(index=True)
    resource_type: str = Field(index=True)
    resource_id: Optional[str] = Field(default=None, index=True)
    
    # Status/Result
    result: str = Field(index=True)  # success | failure | blocked (Legacy, kept for compat)
    status: Optional[str] = Field(default=None, index=True) # SUCCESS | DENIED | FAILED (Task 4 Standard)
    
    # Reason
    reason: Optional[str] = None # Task 4: Mandatory for mutations

    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None # Task 4

    # Data Snapshots
    details: Dict = Field(default={}, sa_column=Column(JSON)) # Legacy bucket
    
    # Structured Data (Task 4)
    before_json: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    after_json: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    diff_json: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    metadata_json: Optional[Dict] = Field(default=None, sa_column=Column(JSON))

    # Error Tracking
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    # Hash Chain
    row_hash: Optional[str] = Field(default=None, index=True)
    prev_row_hash: Optional[str] = Field(default=None, index=True)
    chain_id: Optional[str] = Field(default=None, index=True)
    sequence: Optional[int] = Field(default=None, index=True)

    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow(), index=True)

# Affiliate moved to growth_models.py
from app.models.growth_models import Affiliate
from app.models.game_import_sql import GameImportJob, GameImportItem
from app.models.reports_sql import ReportExportJob
from app.models.simulation_sql import SimulationRun


class RiskRule(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    name: str
    condition: str # "amount > 1000"
    action: str # "flag"
    is_active: bool = True


class ApprovalRequest(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    type: str # withdrawal
    related_entity_id: str
    requester_id: str
    status: str = "pending"
    details: Dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())


class ContentPage(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    slug: str
    title: str
    content: str = Field(sa_column=Column(Text))
    status: str = "published"
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

# --- GAME CONFIG & ASSET MODELS (EXTENDED) ---

class GameConfigVersion(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    game_id: str = Field(foreign_key="game.id", index=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    version: str
    config_snapshot: Dict = Field(default={}, sa_column=Column(JSON))
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class GameAsset(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    game_id: str = Field(foreign_key="game.id", index=True)
    asset_type: str # image, video, sound
    url: str
    metadata_json: Dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

# --- PAYOUT ATTEMPTS (P0-5) ---

class PayoutAttempt(SQLModel, table=True):
    """Tracks each attempt to send a withdrawal payout to a PSP.

    This decouples withdrawal review from the actual provider payout so that we
    can model retries, failures and webhook replay safety.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

    # Which withdrawal this attempt belongs to
    withdraw_tx_id: str = Field(foreign_key="transaction.id", index=True)

    # Tenant scoping (copied from the parent transaction for convenience)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)

    # PSP information
    provider: str = Field(index=True)
    provider_event_id: Optional[str] = Field(default=None, index=True)

    # Idempotency for start_payout calls
    idempotency_key: Optional[str] = Field(default=None, index=True)

    status: str = Field(default="pending", index=True)
    error_code: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())


# --- FINANCE MODELS (EXTENDED) ---

class ReconciliationReport(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    provider_name: str
    period_start: datetime
    period_end: datetime
    total_records: int = 0
    mismatches: int = 0
    status: str = "pending"
    report_data: Dict = Field(default={}, sa_column=Column(JSON)) # Items, summary
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class ChargebackCase(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True)
    transaction_id: str = Field(foreign_key="transaction.id", index=True)
    reason_code: str
    status: str = "open"
    evidence_files: List[str] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class FinanceSettings(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.id", index=True, unique=True)
    auto_payout_limit: float = 0.0
    provider_configs: Dict = Field(default={}, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())


# --- MISC TABLES (moved from route modules to keep Alembic metadata complete) ---

class APIKey(SQLModel, table=True):
    __tablename__ = "apikey"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    tenant_id: str = Field(index=True)
    name: str
    key_hash: str
    scopes: str  # comma-separated
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())


class FeatureFlag(SQLModel, table=True):
    __tablename__ = "featureflag"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    key: str
    description: str
    is_enabled: bool = False
    created_at: str = ""

# LedgerTransaction and WalletBalance moved to repositories/ledger_repo.py to avoid duplicates
from app.repositories.ledger_repo import LedgerTransaction, WalletBalance

