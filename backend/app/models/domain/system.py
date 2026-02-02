from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# --- SYSTEM LOGS ---

class LogSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"

class JobStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"
    RUNNING = "running"

class DeployStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    ROLLBACK = "rollback"
    CANCELED = "canceled"

class SystemEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
    module: str
    severity: LogSeverity
    event_type: str
    message: str
    host: Optional[str] = None
    correlation_id: Optional[str] = None

class CronLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_name: str
    job_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: JobStatus = JobStatus.RUNNING
    error_message: Optional[str] = None

class ServiceHealth(BaseModel):
    service_name: str
    status: ServiceStatus
    latency_ms: float
    error_rate: float
    instance_count: int
    last_heartbeat: datetime = Field(default_factory=lambda: datetime.utcnow())

class DeploymentLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    environment: str
    service: str
    version: str
    initiated_by: str
    status: DeployStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    changelog: str

class ConfigChangeLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
    admin_id: str
    target: str
    diff: Dict[str, Any] 
    severity: LogSeverity
    requires_restart: bool = False

class ErrorLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
    service: str
    error_type: str
    severity: LogSeverity
    message: str
    stack_trace: Optional[str] = None
    impact_users: int = 0
    correlation_id: Optional[str] = None

class QueueLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    queue_name: str
    payload_type: str
    started_at: datetime
    duration_ms: float
    retries: int = 0
    status: str
    error: Optional[str] = None

class DBLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
    execution_time_ms: float
    query_snippet: str
    affected_rows: int
    is_slow: bool = False

class CacheLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
    cache_type: str 
    operation: str 
    key: str
    ttl: int

class LogArchive(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    log_type: str
    date_range: str
    size_mb: float
    storage_type: str 
    status: str 

class SystemLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    level: str 
    service: str 
    message: str
    details: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
