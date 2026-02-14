from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from enum import Enum

class ReconciliationStatus(str, Enum):
    MATCHED = "matched"
    MISMATCH_AMOUNT = "mismatch_amount"
    MISSING_IN_DB = "missing_in_db"
    MISSING_IN_PROVIDER = "missing_in_provider"
    PENDING = "pending"
    POTENTIAL_FRAUD = "potential_fraud" # New Risk Status

class ReconciliationItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_id: Optional[str] = None
    provider_ref: str
    
    # Amounts
    db_amount: Optional[float] = None
    provider_amount: Optional[float] = None
    difference: float = 0.0
    
    # Multi-Currency Support
    original_currency: str = "USD"
    converted_amount: Optional[float] = None
    exchange_rate: float = 1.0
    
    status: ReconciliationStatus
    risk_flag: bool = False # Linked to Fraud
    notes: Optional[str] = None

class ReconciliationSchedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: str
    frequency: str = "daily" # hourly, daily, weekly
    auto_fetch_enabled: bool = False
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    api_credentials_enc: Optional[str] = None # Mock encrypted string

class ReconciliationReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_name: str
    file_name: str = "Auto-Fetch"
    period_start: datetime
    period_end: datetime
    total_records: int = 0
    mismatches: int = 0
    fraud_alerts: int = 0 # New Metric
    currency_mismatches: int = 0 # New Metric
    status: str = "processing" 
    items: List[ReconciliationItem] = []
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class ChargebackStatus(str, Enum):
    OPEN = "open"
    EVIDENCE_GATHERING = "evidence_gathering"
    EVIDENCE_SUBMITTED = "evidence_submitted"
    WON = "won"
    LOST = "lost"

class ChargebackCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_id: str
    player_id: str
    amount: float
    reason_code: str
    status: ChargebackStatus = ChargebackStatus.OPEN
    due_date: datetime
    
    # Fraud Integration
    risk_score_at_time: int = 0
    fraud_cluster_id: Optional[str] = None
    
    evidence_files: List[str] = []
    notes: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class AuditLogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    action: str
    target_id: str
    target_type: str
    details: str
    ip_address: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
