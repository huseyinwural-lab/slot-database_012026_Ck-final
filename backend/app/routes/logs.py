from fastapi import APIRouter, HTTPException, Body, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import random
from app.models.modules import (
    SystemEvent, CronLog, ServiceHealth, DeploymentLog, ConfigChangeLog, ErrorLog, 
    QueueLog, DBLog, CacheLog, LogArchive,
    LogSeverity, ServiceStatus, JobStatus, DeployStatus
)
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- SYSTEM EVENTS ---
@router.get("/events", response_model=List[SystemEvent])
async def get_system_events(severity: Optional[str] = None):
    db = get_db()
    query = {}
    if severity: query["severity"] = severity
    return [SystemEvent(**e) for e in await db.log_events.find(query).sort("timestamp", -1).limit(100).to_list(100)]

@router.post("/events")
async def create_event(event: SystemEvent):
    db = get_db()
    await db.log_events.insert_one(event.model_dump())
    return event

# --- CRON JOBS ---
@router.get("/cron", response_model=List[CronLog])
async def get_cron_logs():
    db = get_db()
    return [CronLog(**c) for c in await db.log_cron.find().sort("started_at", -1).limit(100).to_list(100)]

@router.post("/cron/run")
async def run_cron_job(job_name: str = Body(..., embed=True)):
    # Mock run
    log = CronLog(job_name=job_name, job_id=str(uuid.uuid4()), started_at=datetime.now(timezone.utc), status=JobStatus.RUNNING)
    db = get_db()
    await db.log_cron.insert_one(log.model_dump())
    # ... finish
    log.status = JobStatus.SUCCESS
    log.finished_at = datetime.now(timezone.utc)
    log.duration_ms = 150
    await db.log_cron.update_one({"id": log.id}, {"$set": log.model_dump()})
    return log

# --- SERVICE HEALTH ---
@router.get("/health", response_model=List[ServiceHealth])
async def get_service_health():
    return [
        ServiceHealth(service_name="Payment Gateway", status=ServiceStatus.HEALTHY, latency_ms=45, error_rate=0.1, instance_count=3),
        ServiceHealth(service_name="Game Engine", status=ServiceStatus.HEALTHY, latency_ms=120, error_rate=0.5, instance_count=10),
        ServiceHealth(service_name="Risk Engine", status=ServiceStatus.DEGRADED, latency_ms=500, error_rate=2.0, instance_count=2),
    ]

# --- DEPLOYMENT ---
@router.get("/deployments", response_model=List[DeploymentLog])
async def get_deployments():
    db = get_db()
    return [DeploymentLog(**d) for d in await db.log_deployments.find().sort("start_time", -1).limit(20).to_list(20)]

# --- CONFIG CHANGES ---
@router.get("/config", response_model=List[ConfigChangeLog])
async def get_config_logs():
    db = get_db()
    return [ConfigChangeLog(**c) for c in await db.log_config.find().sort("timestamp", -1).limit(50).to_list(50)]

# --- ERRORS ---
@router.get("/errors", response_model=List[ErrorLog])
async def get_error_logs(severity: Optional[str] = None):
    db = get_db()
    query = {}
    if severity: query["severity"] = severity
    return [ErrorLog(**e) for e in await db.log_errors.find(query).sort("timestamp", -1).limit(100).to_list(100)]

# --- QUEUES ---
@router.get("/queues", response_model=List[QueueLog])
async def get_queue_logs():
    db = get_db()
    return [QueueLog(**q) for q in await db.log_queues.find().sort("started_at", -1).limit(100).to_list(100)]

# --- DB & CACHE ---
@router.get("/db", response_model=List[DBLog])
async def get_db_logs(slow_only: bool = False):
    db = get_db()
    query = {"is_slow": True} if slow_only else {}
    return [DBLog(**l) for l in await db.log_db.find(query).sort("timestamp", -1).limit(100).to_list(100)]

@router.get("/cache", response_model=List[CacheLog])
async def get_cache_logs():
    db = get_db()
    return [CacheLog(**c) for c in await db.log_cache.find().sort("timestamp", -1).limit(100).to_list(100)]

# --- ARCHIVE ---
@router.get("/archive", response_model=List[LogArchive])
async def get_archives():
    db = get_db()
    return [LogArchive(**a) for a in await db.log_archive.find().to_list(100)]

# --- SEED ---
@router.post("/seed")
async def seed_logs():
    db = get_db()
    if await db.log_events.count_documents({}) == 0:
        await db.log_events.insert_one(SystemEvent(module="System", severity=LogSeverity.INFO, event_type="startup", message="System Started").model_dump())
    if await db.log_deployments.count_documents({}) == 0:
        await db.log_deployments.insert_one(DeploymentLog(environment="prod", service="backend", version="v1.0.0", initiated_by="CI/CD", status=DeployStatus.SUCCESS, start_time=datetime.now(timezone.utc), changelog="Initial release").model_dump())
    if await db.log_errors.count_documents({}) == 0:
        await db.log_errors.insert_one(ErrorLog(service="Payment", error_type="Timeout", severity=LogSeverity.ERROR, message="Gateway timed out").model_dump())
    return {"message": "Logs Seeded"}
