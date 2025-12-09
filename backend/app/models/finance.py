from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from enum import Enum

# Use existing Enums from core if possible, but redefine for standalone if needed to avoid circular imports.
# For now, I will define specific ones.

class ReconciliationStatus(str, Enum):
    MATCHED = "matched"
    MISMATCH_AMOUNT = "mismatch_amount"
    MISSING_IN_DB = "missing_in_db"
    MISSING_IN_PROVIDER = "missing_in_provider"
    PENDING = "pending"

class ReconciliationItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_id: Optional[str] = None
    provider_ref: str
    db_amount: Optional[float] = None
    provider_amount: Optional[float] = None
    status: ReconciliationStatus
    difference: float = 0.0
    
class ReconciliationReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_name: str
    file_name: str
    period_start: datetime
    period_end: datetime
    total_records: int = 0
    mismatches: int = 0
    status: str = "processing" # processing, completed
    items: List[ReconciliationItem] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    evidence_files: List[str] = [] # URLs
    notes: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AuditLogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    action: str # "approve", "reject", "upload_evidence"
    target_id: str
    target_type: str # "transaction", "chargeback"
    details: str
    ip_address: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
