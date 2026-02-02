from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

# --- REPORTS MODELS ---

class ReportSchedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str 
    frequency: str 
    recipients: List[str] = []
    format: str = "pdf"
    next_run: datetime
    active: bool = True

class ExportJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    status: str = "processing" 
    requested_by: str
    download_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
