from fastapi import APIRouter, HTTPException, Body, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import random
from app.models.modules import (
    SimulationRun, GameMathSimulation, PortfolioSimulation, BonusSimulation,
    CohortLTVSimulation, RiskSimulation, RGSimulation, ABVariantSimulation,
    ScenarioBuilder, SimulationType, SimulationStatus, GameType
)
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1/simulation-lab", tags=["simulation_lab"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- SIMULATION RUNS (Overview & Archive) ---
@router.get("/runs", response_model=List[SimulationRun])
async def get_simulation_runs(
    simulation_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=200)
):
    db = get_db()
    query = {}
    if simulation_type:
        query["simulation_type"] = simulation_type
    if status:
        query["status"] = status
    
    runs = await db.simulation_runs.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    return [SimulationRun(**r) for r in runs]

@router.post("/runs", response_model=SimulationRun)
async def create_simulation_run(run: SimulationRun):
    db = get_db()
    run.created_at = datetime.now(timezone.utc)
    await db.simulation_runs.insert_one(run.model_dump())
    return run

@router.get("/runs/{run_id}", response_model=SimulationRun)
async def get_simulation_run(run_id: str):
    db = get_db()
    run = await db.simulation_runs.find_one({"id": run_id})
    if not run:
        raise HTTPException(404, "Simulation run not found")
    return SimulationRun(**run)

@router.delete("/runs/{run_id}")
async def delete_simulation_run(run_id: str):
    db = get_db()
    result = await db.simulation_runs.delete_one({"id": run_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Run not found")
    return {"message": "Simulation run deleted"}

# --- GAME MATH SIMULATOR ---
@router.post("/game-math", response_model=GameMathSimulation)
async def run_game_math_simulation(simulation: GameMathSimulation):
    db = get_db()
    
    # Mock simulation logic
    total_bet = simulation.spins_to_simulate * 1.0  # Assume $1 per spin
    rtp = simulation.rtp_override or 96.5
    total_win = total_bet * (rtp / 100)
    
    # Add randomness
    total_win *= random.uniform(0.95, 1.05)
    simulated_rtp = (total_win / total_bet) * 100
    
    simulation.results = {
        "total_spins": simulation.spins_to_simulate,
        "total_bet": total_bet,
        "total_win": round(total_win, 2),
        "simulated_rtp": round(simulated_rtp, 2),
        "volatility": round(random.uniform(3.0, 9.0), 2),
        "hit_frequency": round(random.uniform(20, 45), 2),
        "bonus_hit_frequency": round(random.uniform(1, 5), 2),
        "max_single_win": round(total_bet * random.uniform(500, 2000), 2)
    }
    
    simulation.distribution = {
        "0x": random.randint(int(simulation.spins_to_simulate * 0.4), int(simulation.spins_to_simulate * 0.6)),
        "0-1x": random.randint(int(simulation.spins_to_simulate * 0.2), int(simulation.spins_to_simulate * 0.3)),
        "1-10x": random.randint(int(simulation.spins_to_simulate * 0.05), int(simulation.spins_to_simulate * 0.15)),
        "10-50x": random.randint(int(simulation.spins_to_simulate * 0.01), int(simulation.spins_to_simulate * 0.05)),
        "50-100x": random.randint(1, int(simulation.spins_to_simulate * 0.01)),
        "100x+": random.randint(0, int(simulation.spins_to_simulate * 0.001))
    }
    
    await db.game_math_simulations.insert_one(simulation.model_dump())
    
    # Update run status
    await db.simulation_runs.update_one(
        {"id": simulation.run_id},
        {"$set": {"status": SimulationStatus.COMPLETED, "completed_at": datetime.now(timezone.utc)}}
    )
    
    return simulation

@router.get("/game-math/{run_id}", response_model=List[GameMathSimulation])
async def get_game_math_simulations(run_id: str):
    db = get_db()
    sims = await db.game_math_simulations.find({"run_id": run_id}).to_list(100)
    return [GameMathSimulation(**s) for s in sims]

# --- PORTFOLIO SIMULATOR ---
@router.post("/portfolio", response_model=PortfolioSimulation)
async def run_portfolio_simulation(simulation: PortfolioSimulation):
    db = get_db()
    
    # Mock calculation
    current_total_revenue = sum(g.get("traffic_share", 0) * g.get("expected_revenue", 1000) for g in simulation.games)
    simulated_total_revenue = sum(g.get("new_traffic", 0) * g.get("expected_revenue", 1000) * (g.get("new_rtp", 96) / g.get("current_rtp", 96)) for g in simulation.games)
    
    simulation.current_ggr = round(current_total_revenue, 2)
    simulation.simulated_ggr = round(simulated_total_revenue, 2)
    simulation.current_ngr = round(current_total_revenue * 0.85, 2)
    simulation.simulated_ngr = round(simulated_total_revenue * 0.85, 2)
    simulation.jackpot_cost = round(simulated_total_revenue * 0.02, 2)
    simulation.bonus_cost = round(simulated_total_revenue * 0.05, 2)
    
    await db.portfolio_simulations.insert_one(simulation.model_dump())
    
    await db.simulation_runs.update_one(
        {"id": simulation.run_id},
        {"$set": {"status": SimulationStatus.COMPLETED, "completed_at": datetime.now(timezone.utc)}}
    )
    
    return simulation

# --- BONUS SIMULATOR ---
@router.post("/bonus", response_model=BonusSimulation)
async def run_bonus_simulation(simulation: BonusSimulation):
    db = get_db()
    
    # Mock calculation
    total_issued = simulation.expected_participants * (simulation.new_percentage / 100) * 100
    used = total_issued * 0.75
    liabilities = used * simulation.new_wagering
    additional_ggr = liabilities * 0.15
    net_cost = used - additional_ggr
    roi = ((additional_ggr - net_cost) / net_cost) * 100 if net_cost > 0 else 0
    
    simulation.results = {
        "total_issued": round(total_issued, 2),
        "bonus_used": round(used, 2),
        "liabilities": round(liabilities, 2),
        "additional_ggr": round(additional_ggr, 2),
        "net_cost": round(net_cost, 2),
        "roi": round(roi, 2),
        "abuse_rate": round(random.uniform(2, 8), 2),
        "fraud_flags": random.randint(5, 25)
    }
    
    await db.bonus_simulations.insert_one(simulation.model_dump())
    
    await db.simulation_runs.update_one(
        {"id": simulation.run_id},
        {"$set": {"status": SimulationStatus.COMPLETED, "completed_at": datetime.now(timezone.utc)}}
    )
    
    return simulation

# --- COHORT/LTV SIMULATOR ---
@router.post("/cohort-ltv", response_model=CohortLTVSimulation)
async def run_cohort_ltv_simulation(simulation: CohortLTVSimulation):
    db = get_db()
    
    # Mock LTV calculation
    baseline = simulation.baseline_ltv
    policy_multiplier = 1.0
    
    if simulation.policy_changes.get("increased_welcome_bonus"):
        policy_multiplier *= 1.15
    if simulation.policy_changes.get("reduced_cashback"):
        policy_multiplier *= 0.95
    
    simulation.simulated_ltv = round(baseline * policy_multiplier, 2)
    simulation.deposit_frequency = round(random.uniform(3, 8), 2)
    simulation.churn_rate = round(random.uniform(15, 35), 2)
    simulation.bonus_cost = round(simulation.simulated_ltv * 0.12, 2)
    simulation.rg_flag_rate = round(random.uniform(2, 6), 2)
    simulation.fraud_risk_impact = round(random.uniform(0.5, 2.5), 2)
    
    await db.cohort_ltv_simulations.insert_one(simulation.model_dump())
    
    await db.simulation_runs.update_one(
        {"id": simulation.run_id},
        {"$set": {"status": SimulationStatus.COMPLETED, "completed_at": datetime.now(timezone.utc)}}
    )
    
    return simulation

# --- RISK SIMULATOR ---
@router.post("/risk", response_model=RiskSimulation)
async def run_risk_simulation(simulation: RiskSimulation):
    db = get_db()
    
    # Mock risk calculation
    simulation.total_alerts_current = random.randint(500, 1500)
    simulation.total_alerts_simulated = int(simulation.total_alerts_current * random.uniform(0.7, 1.3))
    simulation.fraud_caught = int(simulation.total_alerts_simulated * 0.15)
    simulation.false_positives = int(simulation.total_alerts_simulated * 0.25)
    simulation.auto_freeze_count = int(simulation.fraud_caught * 0.6)
    simulation.withdrawal_blocks = int(simulation.fraud_caught * 0.4)
    simulation.lost_revenue = round(simulation.false_positives * 50.0, 2)
    
    await db.risk_simulations.insert_one(simulation.model_dump())
    
    await db.simulation_runs.update_one(
        {"id": simulation.run_id},
        {"$set": {"status": SimulationStatus.COMPLETED, "completed_at": datetime.now(timezone.utc)}}
    )
    
    return simulation

# --- RG SIMULATOR ---
@router.post("/rg", response_model=RGSimulation)
async def run_rg_simulation(simulation: RGSimulation):
    db = get_db()
    
    # Mock RG impact
    simulation.affected_players = random.randint(100, 500)
    simulation.deposits_reduction = round(random.uniform(5000, 15000), 2)
    simulation.high_loss_reduced = round(random.uniform(10000, 30000), 2)
    simulation.revenue_impact = round(simulation.deposits_reduction * -0.15, 2)
    simulation.players_hitting_limit_current = random.randint(50, 150)
    simulation.players_hitting_limit_simulated = int(simulation.players_hitting_limit_current * 1.4)
    
    await db.rg_simulations.insert_one(simulation.model_dump())
    
    await db.simulation_runs.update_one(
        {"id": simulation.run_id},
        {"$set": {"status": SimulationStatus.COMPLETED, "completed_at": datetime.now(timezone.utc)}}
    )
    
    return simulation

# --- A/B VARIANT SANDBOX ---
@router.post("/ab-variant", response_model=ABVariantSimulation)
async def run_ab_variant_simulation(simulation: ABVariantSimulation):
    db = get_db()
    
    # Mock A/B results
    simulation.conversion_uplift = round(random.uniform(-5, 25), 2)
    simulation.revenue_uplift = round(random.uniform(-3, 18), 2)
    simulation.risk_uptick = round(random.uniform(0, 3), 2)
    
    await db.ab_variant_simulations.insert_one(simulation.model_dump())
    
    await db.simulation_runs.update_one(
        {"id": simulation.run_id},
        {"$set": {"status": SimulationStatus.COMPLETED, "completed_at": datetime.now(timezone.utc)}}
    )
    
    return simulation

# --- SCENARIO BUILDER ---
@router.post("/scenario", response_model=ScenarioBuilder)
async def run_scenario_builder(scenario: ScenarioBuilder):
    db = get_db()
    
    # Mock multi-module calculation
    total_revenue_impact = 0.0
    fraud_impact = 0.0
    rg_impact = 0.0
    
    if "games" in scenario.scope:
        total_revenue_impact += random.uniform(5000, 15000)
    if "bonus" in scenario.scope:
        total_revenue_impact -= random.uniform(2000, 8000)
    if "risk" in scenario.scope:
        fraud_impact = random.uniform(-1000, -500)
    if "rg" in scenario.scope:
        rg_impact = random.uniform(-2000, -500)
    
    scenario.consolidated_results = {
        "total_revenue_impact": round(total_revenue_impact, 2),
        "fraud_impact": round(fraud_impact, 2),
        "rg_impact": round(rg_impact, 2),
        "ggr": round(random.uniform(50000, 150000), 2),
        "ngr": round(random.uniform(40000, 120000), 2),
        "bonus_cost": round(random.uniform(5000, 15000), 2),
        "churn_rate": round(random.uniform(15, 30), 2),
        "ltv": round(random.uniform(200, 500), 2)
    }
    
    await db.scenario_builders.insert_one(scenario.model_dump())
    
    await db.simulation_runs.update_one(
        {"id": scenario.run_id},
        {"$set": {"status": SimulationStatus.COMPLETED, "completed_at": datetime.now(timezone.utc)}}
    )
    
    return scenario

# --- SEED ---
@router.post("/seed")
async def seed_simulation_lab():
    db = get_db()
    
    if await db.simulation_runs.count_documents({}) == 0:
        # Create sample runs
        runs = [
            SimulationRun(
                name="Slots RTP Test - Pragmatic Play",
                simulation_type=SimulationType.GAME_MATH,
                status=SimulationStatus.COMPLETED,
                created_by="Admin",
                started_at=datetime.now(timezone.utc) - timedelta(hours=2),
                completed_at=datetime.now(timezone.utc) - timedelta(hours=2, minutes=-5),
                duration_seconds=300,
                notes="Testing RTP variance on 1M spins",
                tags=["slots", "rtp", "production"]
            ),
            SimulationRun(
                name="Q1 Portfolio Revenue Optimization",
                simulation_type=SimulationType.PORTFOLIO,
                status=SimulationStatus.COMPLETED,
                created_by="Finance Team",
                started_at=datetime.now(timezone.utc) - timedelta(days=1),
                completed_at=datetime.now(timezone.utc) - timedelta(days=1, hours=-1),
                duration_seconds=3600,
                notes="Testing traffic reallocation for Q1",
                tags=["portfolio", "revenue", "q1"]
            ),
            SimulationRun(
                name="Welcome Bonus 100% vs 150% Test",
                simulation_type=SimulationType.BONUS,
                status=SimulationStatus.COMPLETED,
                created_by="Marketing",
                started_at=datetime.now(timezone.utc) - timedelta(hours=5),
                completed_at=datetime.now(timezone.utc) - timedelta(hours=5, minutes=-10),
                duration_seconds=600,
                notes="ROI comparison",
                tags=["bonus", "welcome", "ab-test"]
            ),
            SimulationRun(
                name="VIP Player LTV - Increased Cashback Impact",
                simulation_type=SimulationType.COHORT_LTV,
                status=SimulationStatus.RUNNING,
                created_by="CRM Team",
                started_at=datetime.now(timezone.utc) - timedelta(minutes=30),
                notes="90-day LTV projection",
                tags=["ltv", "vip", "cashback"]
            ),
            SimulationRun(
                name="Fraud Rule Tightening Impact",
                simulation_type=SimulationType.RISK,
                status=SimulationStatus.DRAFT,
                created_by="Security",
                notes="Testing stricter device fingerprinting",
                tags=["fraud", "risk", "security"]
            )
        ]
        
        for run in runs:
            await db.simulation_runs.insert_one(run.model_dump())
        
        # Add sample game math simulation
        game_sim = GameMathSimulation(
            run_id=runs[0].id,
            game_type=GameType.SLOTS,
            game_id="slot_001",
            game_name="Big Win Slots",
            spins_to_simulate=1000000,
            rtp_override=96.5,
            results={
                "total_spins": 1000000,
                "total_bet": 1000000.0,
                "total_win": 965234.50,
                "simulated_rtp": 96.52,
                "volatility": 7.2,
                "hit_frequency": 32.5,
                "bonus_hit_frequency": 3.2,
                "max_single_win": 125000.0
            },
            distribution={
                "0x": 450000,
                "0-1x": 320000,
                "1-10x": 180000,
                "10-50x": 40000,
                "50-100x": 8000,
                "100x+": 2000
            }
        )
        await db.game_math_simulations.insert_one(game_sim.model_dump())
    
    return {"message": "Simulation Lab seeded successfully"}
