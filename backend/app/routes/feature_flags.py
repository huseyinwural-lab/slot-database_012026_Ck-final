from fastapi import APIRouter, HTTPException, Body, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import random
from app.models.modules import (
    FeatureFlag, FlagGroup, Segment, Experiment, ExperimentVariant, 
    ExperimentResult, FlagAnalytics, FlagAuditLog, EnvironmentComparison,
    FlagStatus, FlagType, FlagScope, Environment, ExperimentStatus, MetricType
)
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1/flags", tags=["feature_flags"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- FEATURE FLAGS ---
@router.get("/", response_model=List[FeatureFlag])
async def get_feature_flags(
    status: Optional[str] = None,
    group: Optional[str] = None,
    environment: Optional[str] = None
):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if group:
        query["group"] = group
    if environment:
        query["environment"] = environment
    
    flags = await db.feature_flags.find(query).to_list(1000)
    return [FeatureFlag(**f) for f in flags]

@router.post("/", response_model=FeatureFlag)
async def create_feature_flag(flag: FeatureFlag):
    db = get_db()
    flag.created_at = datetime.now(timezone.utc)
    flag.updated_at = datetime.now(timezone.utc)
    await db.feature_flags.insert_one(flag.model_dump())
    
    # Audit log
    audit = FlagAuditLog(
        admin_id="current_admin",
        admin_name="Admin",
        action="created",
        target_type="flag",
        target_id=flag.id,
        target_name=flag.name,
        after_value=flag.model_dump(),
        ip_address="127.0.0.1"
    )
    await db.flag_audit_logs.insert_one(audit.model_dump())
    
    return flag

@router.put("/{flag_id}", response_model=FeatureFlag)
async def update_feature_flag(flag_id: str, flag_update: Dict[str, Any] = Body(...)):
    db = get_db()
    
    # Get current flag
    current = await db.feature_flags.find_one({"id": flag_id})
    if not current:
        raise HTTPException(404, "Flag not found")
    
    flag_update["updated_at"] = datetime.now(timezone.utc)
    await db.feature_flags.update_one({"id": flag_id}, {"$set": flag_update})
    
    # Audit log
    audit = FlagAuditLog(
        admin_id="current_admin",
        admin_name="Admin",
        action="updated",
        target_type="flag",
        target_id=flag_id,
        target_name=current["name"],
        before_value=current,
        after_value=flag_update,
        ip_address="127.0.0.1"
    )
    await db.flag_audit_logs.insert_one(audit.model_dump())
    
    updated = await db.feature_flags.find_one({"id": flag_id})
    return FeatureFlag(**updated)

@router.post("/{flag_id}/toggle")
async def toggle_flag(flag_id: str):
    db = get_db()
    flag = await db.feature_flags.find_one({"id": flag_id})
    if not flag:
        raise HTTPException(404, "Flag not found")
    
    new_status = FlagStatus.OFF if flag["status"] == FlagStatus.ON else FlagStatus.ON
    await db.feature_flags.update_one({"id": flag_id}, {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc)}})
    
    # Audit log
    audit = FlagAuditLog(
        admin_id="current_admin",
        admin_name="Admin",
        action="activated" if new_status == FlagStatus.ON else "deactivated",
        target_type="flag",
        target_id=flag_id,
        target_name=flag["name"],
        ip_address="127.0.0.1"
    )
    await db.flag_audit_logs.insert_one(audit.model_dump())
    
    return {"status": new_status}

@router.delete("/{flag_id}")
async def delete_flag(flag_id: str):
    db = get_db()
    flag = await db.feature_flags.find_one({"id": flag_id})
    if not flag:
        raise HTTPException(404, "Flag not found")
    
    await db.feature_flags.delete_one({"id": flag_id})
    
    # Audit log
    audit = FlagAuditLog(
        admin_id="current_admin",
        admin_name="Admin",
        action="deleted",
        target_type="flag",
        target_id=flag_id,
        target_name=flag["name"],
        before_value=flag,
        ip_address="127.0.0.1"
    )
    await db.flag_audit_logs.insert_one(audit.model_dump())
    
    return {"message": "Flag deleted"}

@router.post("/kill-switch")
async def kill_switch():
    """Emergency: Disable all flags"""
    db = get_db()
    result = await db.feature_flags.update_many(
        {"status": FlagStatus.ON},
        {"$set": {"status": FlagStatus.OFF, "updated_at": datetime.now(timezone.utc)}}
    )
    
    # Audit log
    audit = FlagAuditLog(
        admin_id="current_admin",
        admin_name="Admin",
        action="kill_switch_activated",
        target_type="flag",
        target_id="all",
        target_name="All Flags",
        ip_address="127.0.0.1"
    )
    await db.flag_audit_logs.insert_one(audit.model_dump())
    
    return {"message": f"Disabled {result.modified_count} flags"}

@router.post("/bulk-edit")
async def bulk_edit_flags(flag_ids: List[str] = Body(...), updates: Dict[str, Any] = Body(...)):
    db = get_db()
    updates["updated_at"] = datetime.now(timezone.utc)
    result = await db.feature_flags.update_many(
        {"id": {"$in": flag_ids}},
        {"$set": updates}
    )
    return {"message": f"Updated {result.modified_count} flags"}

# --- FLAG GROUPS ---
@router.get("/groups", response_model=List[FlagGroup])
async def get_flag_groups():
    db = get_db()
    groups = await db.flag_groups.find().to_list(100)
    return [FlagGroup(**g) for g in groups]

@router.post("/groups", response_model=FlagGroup)
async def create_flag_group(group: FlagGroup):
    db = get_db()
    await db.flag_groups.insert_one(group.model_dump())
    return group

# --- SEGMENTS ---
@router.get("/segments", response_model=List[Segment])
async def get_segments():
    db = get_db()
    segments = await db.segments.find().to_list(1000)
    return [Segment(**s) for s in segments]

@router.post("/segments", response_model=Segment)
async def create_segment(segment: Segment):
    db = get_db()
    await db.segments.insert_one(segment.model_dump())
    return segment

@router.put("/segments/{segment_id}", response_model=Segment)
async def update_segment(segment_id: str, segment_update: Dict[str, Any] = Body(...)):
    db = get_db()
    segment_update["updated_at"] = datetime.now(timezone.utc)
    await db.segments.update_one({"id": segment_id}, {"$set": segment_update})
    updated = await db.segments.find_one({"id": segment_id})
    return Segment(**updated)

@router.post("/segments/{segment_id}/test")
async def test_segment(segment_id: str, player_id: str = Body(..., embed=True)):
    """Test if a player matches segment rules"""
    db = get_db()
    segment = await db.segments.find_one({"id": segment_id})
    if not segment:
        raise HTTPException(404, "Segment not found")
    
    # Mock: In real implementation, evaluate rules against player data
    matches = random.choice([True, False])
    return {"player_id": player_id, "matches": matches, "segment_name": segment["name"]}

# --- EXPERIMENTS ---
@router.get("/experiments", response_model=List[Experiment])
async def get_experiments(status: Optional[str] = None):
    db = get_db()
    query = {"status": status} if status else {}
    experiments = await db.experiments.find(query).to_list(1000)
    return [Experiment(**e) for e in experiments]

@router.post("/experiments", response_model=Experiment)
async def create_experiment(experiment: Experiment):
    db = get_db()
    experiment.created_at = datetime.now(timezone.utc)
    experiment.updated_at = datetime.now(timezone.utc)
    await db.experiments.insert_one(experiment.model_dump())
    
    # Audit log
    audit = FlagAuditLog(
        admin_id="current_admin",
        admin_name="Admin",
        action="created",
        target_type="experiment",
        target_id=experiment.id,
        target_name=experiment.name,
        after_value=experiment.model_dump(),
        ip_address="127.0.0.1"
    )
    await db.flag_audit_logs.insert_one(audit.model_dump())
    
    return experiment

@router.put("/experiments/{experiment_id}", response_model=Experiment)
async def update_experiment(experiment_id: str, experiment_update: Dict[str, Any] = Body(...)):
    db = get_db()
    experiment_update["updated_at"] = datetime.now(timezone.utc)
    await db.experiments.update_one({"id": experiment_id}, {"$set": experiment_update})
    updated = await db.experiments.find_one({"id": experiment_id})
    return Experiment(**updated)

@router.post("/experiments/{experiment_id}/start")
async def start_experiment(experiment_id: str):
    db = get_db()
    await db.experiments.update_one(
        {"id": experiment_id},
        {"$set": {"status": ExperimentStatus.RUNNING, "start_date": datetime.now(timezone.utc)}}
    )
    return {"message": "Experiment started"}

@router.post("/experiments/{experiment_id}/pause")
async def pause_experiment(experiment_id: str):
    db = get_db()
    await db.experiments.update_one(
        {"id": experiment_id},
        {"$set": {"status": ExperimentStatus.PAUSED}}
    )
    return {"message": "Experiment paused"}

@router.post("/experiments/{experiment_id}/complete")
async def complete_experiment(experiment_id: str, winner_variant_id: str = Body(..., embed=True)):
    db = get_db()
    await db.experiments.update_one(
        {"id": experiment_id},
        {"$set": {"status": ExperimentStatus.COMPLETED, "end_date": datetime.now(timezone.utc)}}
    )
    
    # Mark winner
    await db.experiment_results.update_many(
        {"experiment_id": experiment_id},
        {"$set": {"is_winner": False}}
    )
    await db.experiment_results.update_one(
        {"experiment_id": experiment_id, "variant_id": winner_variant_id},
        {"$set": {"is_winner": True}}
    )
    
    return {"message": "Experiment completed"}

# --- EXPERIMENT RESULTS ---
@router.get("/experiments/{experiment_id}/results", response_model=List[ExperimentResult])
async def get_experiment_results(experiment_id: str):
    db = get_db()
    results = await db.experiment_results.find({"experiment_id": experiment_id}).to_list(100)
    return [ExperimentResult(**r) for r in results]

@router.post("/experiments/{experiment_id}/results", response_model=ExperimentResult)
async def create_experiment_result(experiment_id: str, result: ExperimentResult):
    db = get_db()
    result.experiment_id = experiment_id
    await db.experiment_results.insert_one(result.model_dump())
    return result

# --- ANALYTICS ---
@router.get("/analytics/{flag_id}", response_model=List[FlagAnalytics])
async def get_flag_analytics(flag_id: str, days: int = Query(7, le=90)):
    db = get_db()
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    analytics = await db.flag_analytics.find({
        "flag_id": flag_id,
        "date": {"$gte": start_date}
    }).to_list(1000)
    return [FlagAnalytics(**a) for a in analytics]

# --- AUDIT LOG ---
@router.get("/audit-log", response_model=List[FlagAuditLog])
async def get_flag_audit_log(
    target_type: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    db = get_db()
    query = {}
    if target_type:
        query["target_type"] = target_type
    if action:
        query["action"] = action
    
    logs = await db.flag_audit_logs.find(query).sort("timestamp", -1).limit(limit).to_list(limit)
    return [FlagAuditLog(**log) for log in logs]

# --- ENVIRONMENT COMPARISON ---
@router.get("/environment-comparison", response_model=List[EnvironmentComparison])
async def compare_environments():
    db = get_db()
    
    # Get all flags from both environments
    prod_flags = await db.feature_flags.find({"environment": Environment.PRODUCTION}).to_list(1000)
    staging_flags = await db.feature_flags.find({"environment": Environment.STAGING}).to_list(1000)
    
    comparisons = []
    prod_dict = {f["flag_id"]: f for f in prod_flags}
    staging_dict = {f["flag_id"]: f for f in staging_flags}
    
    all_flag_ids = set(prod_dict.keys()) | set(staging_dict.keys())
    
    for flag_id in all_flag_ids:
        prod_data = prod_dict.get(flag_id, {})
        staging_data = staging_dict.get(flag_id, {})
        
        differences = []
        if not prod_data:
            differences.append("Only in staging")
        elif not staging_data:
            differences.append("Only in production")
        else:
            if prod_data.get("status") != staging_data.get("status"):
                differences.append(f"Status: {prod_data.get('status')} vs {staging_data.get('status')}")
            if prod_data.get("default_value") != staging_data.get("default_value"):
                differences.append(f"Value: {prod_data.get('default_value')} vs {staging_data.get('default_value')}")
        
        if differences or prod_data or staging_data:
            comp = EnvironmentComparison(
                flag_id=flag_id,
                flag_name=prod_data.get("name") or staging_data.get("name", "Unknown"),
                production=prod_data,
                staging=staging_data,
                differences=differences
            )
            comparisons.append(comp)
    
    return comparisons

# --- SEED ---
@router.post("/seed")
async def seed_feature_flags():
    db = get_db()
    
    # Seed Flag Groups
    if await db.flag_groups.count_documents({}) == 0:
        groups = [
            FlagGroup(name="Payments", description="Payment flow features", flag_count=0),
            FlagGroup(name="Games", description="Game-related features", flag_count=0),
            FlagGroup(name="Fraud", description="Fraud detection features", flag_count=0),
            FlagGroup(name="CMS", description="Content management features", flag_count=0),
            FlagGroup(name="CRM", description="CRM and communication features", flag_count=0)
        ]
        for group in groups:
            await db.flag_groups.insert_one(group.model_dump())
    
    # Seed Feature Flags
    if await db.feature_flags.count_documents({}) == 0:
        flags = [
            FeatureFlag(
                flag_id="new_payment_flow",
                name="New Payment Flow",
                description="Enable redesigned payment checkout",
                status=FlagStatus.ON,
                type=FlagType.BOOLEAN,
                default_value=True,
                scope=FlagScope.FRONTEND,
                environment=Environment.PRODUCTION,
                targeting={"rollout_percentage": 50, "countries": ["TR", "DE"]},
                group="Payments",
                last_updated_by="Admin"
            ),
            FeatureFlag(
                flag_id="game_recommendations",
                name="AI Game Recommendations",
                description="ML-based game suggestions",
                status=FlagStatus.OFF,
                type=FlagType.BOOLEAN,
                default_value=False,
                scope=FlagScope.BOTH,
                environment=Environment.PRODUCTION,
                targeting={"rollout_percentage": 10, "vip_levels": [3, 4, 5]},
                group="Games",
                last_updated_by="Admin"
            ),
            FeatureFlag(
                flag_id="enhanced_fraud_detection",
                name="Enhanced Fraud Detection",
                description="Advanced fraud rules with AI",
                status=FlagStatus.ON,
                type=FlagType.BOOLEAN,
                default_value=True,
                scope=FlagScope.BACKEND,
                environment=Environment.PRODUCTION,
                targeting={},
                group="Fraud",
                last_updated_by="Admin"
            ),
            FeatureFlag(
                flag_id="dynamic_bonus_offers",
                name="Dynamic Bonus Offers",
                description="Personalized bonus recommendations",
                status=FlagStatus.SCHEDULED,
                type=FlagType.JSON,
                default_value={"enabled": False},
                scope=FlagScope.BOTH,
                environment=Environment.STAGING,
                targeting={"rollout_percentage": 25},
                group="CRM",
                last_updated_by="Admin",
                scheduled_activation=datetime.now(timezone.utc) + timedelta(days=7)
            )
        ]
        for flag in flags:
            await db.feature_flags.insert_one(flag.model_dump())
    
    # Seed Segments
    if await db.segments.count_documents({}) == 0:
        segments = [
            Segment(
                name="VIP Players",
                description="High-value players with VIP status",
                rules=[
                    {"field": "vip_level", "operator": ">=", "value": 3},
                    {"field": "total_deposits", "operator": ">", "value": 10000}
                ],
                population_size=1250,
                usage_count=3
            ),
            Segment(
                name="New Players",
                description="Players registered in last 30 days",
                rules=[
                    {"field": "registration_date", "operator": ">=", "value": "30_days_ago"},
                    {"field": "deposit_count", "operator": "<=", "value": 2}
                ],
                population_size=5600,
                usage_count=5
            ),
            Segment(
                name="High Rollers",
                description="Players with large bet amounts",
                rules=[
                    {"field": "avg_bet", "operator": ">", "value": 100},
                    {"field": "session_count", "operator": ">", "value": 50}
                ],
                population_size=450,
                usage_count=2
            )
        ]
        for segment in segments:
            await db.segments.insert_one(segment.model_dump())
    
    # Seed Experiments
    if await db.experiments.count_documents({}) == 0:
        variants_a = [
            ExperimentVariant(name="Control (A)", traffic_percentage=50.0, description="Current implementation"),
            ExperimentVariant(name="Variant B", traffic_percentage=50.0, description="New design with larger CTA")
        ]
        
        experiments = [
            Experiment(
                name="Deposit Button Color Test",
                description="Testing green vs blue deposit button",
                status=ExperimentStatus.RUNNING,
                variants=variants_a,
                targeting={"countries": ["TR"], "new_users": True},
                primary_metric=MetricType.CONVERSION,
                secondary_metrics=[MetricType.CTR, MetricType.DEPOSIT],
                min_sample_size=5000,
                start_date=datetime.now(timezone.utc) - timedelta(days=5),
                owner="Marketing Team"
            ),
            Experiment(
                name="Game Lobby Layout",
                description="Grid vs List view for game lobby",
                status=ExperimentStatus.COMPLETED,
                variants=[
                    ExperimentVariant(name="Grid View (A)", traffic_percentage=50.0),
                    ExperimentVariant(name="List View (B)", traffic_percentage=50.0)
                ],
                targeting={},
                primary_metric=MetricType.SESSION_TIME,
                secondary_metrics=[MetricType.GAME_REVENUE],
                min_sample_size=10000,
                start_date=datetime.now(timezone.utc) - timedelta(days=30),
                end_date=datetime.now(timezone.utc) - timedelta(days=5),
                owner="Product Team"
            )
        ]
        for exp in experiments:
            await db.experiments.insert_one(exp.model_dump())
            
            # Seed results for completed experiment
            if exp.status == ExperimentStatus.COMPLETED:
                results = [
                    ExperimentResult(
                        experiment_id=exp.id,
                        variant_id=exp.variants[0].id,
                        variant_name="Grid View (A)",
                        users_exposed=12500,
                        conversions=1875,
                        conversion_rate=15.0,
                        revenue=125000.0,
                        deposit_count=1250,
                        statistical_confidence=95.5,
                        is_winner=True
                    ),
                    ExperimentResult(
                        experiment_id=exp.id,
                        variant_id=exp.variants[1].id,
                        variant_name="List View (B)",
                        users_exposed=12500,
                        conversions=1500,
                        conversion_rate=12.0,
                        revenue=95000.0,
                        deposit_count=1000,
                        statistical_confidence=95.5,
                        is_winner=False
                    )
                ]
                for result in results:
                    await db.experiment_results.insert_one(result.model_dump())
    
    return {"message": "Feature Flags & Experiments seeded successfully"}
