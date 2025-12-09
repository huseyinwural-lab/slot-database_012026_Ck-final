from fastapi import APIRouter, HTTPException, UploadFile, File, Body
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import csv
import io
import random
from app.models.finance import (
    ReconciliationReport, ReconciliationItem, ChargebackCase, 
    ChargebackStatus, AuditLogEntry, ReconciliationSchedule
)
from app.models.core import Transaction
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1/finance", tags=["finance_advanced"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- RECONCILIATION LOGIC ---

@router.post("/reconciliation/upload", response_model=ReconciliationReport)
async def upload_reconciliation(
    provider: str, 
    file: UploadFile = File(...),
    currency_col: str = "currency", # CSV column name
    amount_col: str = "amount",
    id_col: str = "tx_id"
):
    db = get_db()
    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    
    report = ReconciliationReport(
        provider_name=provider,
        file_name=file.filename,
        period_start=datetime.now(timezone.utc), 
        period_end=datetime.now(timezone.utc)
    )
    
    items = []
    
    # Mock FX Rates
    fx_rates = {"EUR": 1.10, "TRY": 0.03, "USD": 1.0}
    
    for row in reader:
        ref_id = row.get(id_col, 'unknown')
        raw_amount = float(row.get(amount_col, 0))
        currency = row.get(currency_col, "USD")
        
        # FX Conversion
        rate = fx_rates.get(currency, 1.0)
        converted_amt = raw_amount * rate
        
        # Check DB
        tx = await db.transactions.find_one({"provider_tx_id": ref_id})
        
        item = ReconciliationItem(
            provider_ref=ref_id,
            provider_amount=raw_amount,
            original_currency=currency,
            exchange_rate=rate,
            converted_amount=converted_amt
        )

        if not tx:
            # Check for Adjustment Match (Manual Adjustment Integration)
            adj = await db.transactions.find_one({
                "type": "adjustment", 
                "amount": {"$gte": converted_amt - 1, "$lte": converted_amt + 1},
                "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=2)}
            })
            
            if adj:
                item.status = "matched"
                item.notes = f"Matched with Manual Adjustment {adj['id']}"
                item.transaction_id = adj['id']
                item.db_amount = adj['amount']
            else:
                item.status = "missing_in_db"
                item.difference = converted_amt
                # Fraud Check
                if converted_amt > 5000:
                    item.status = "potential_fraud"
                    item.risk_flag = True
                    item.notes = "High value missing transaction - Potential Fraud"
                    report.fraud_alerts += 1
        
        else:
            # Found TX
            item.transaction_id = tx['id']
            item.db_amount = tx['amount']
            
            diff = abs(tx['amount'] - converted_amt)
            if diff > (tx['amount'] * 0.02): # 2% tolerance
                item.status = "mismatch_amount"
                item.difference = tx['amount'] - converted_amt
            else:
                item.status = "matched"
                
        items.append(item)
            
    report.items = items
    report.total_records = len(items)
    report.mismatches = len([i for i in items if i.status != "matched"])
    report.status = "completed"
    
    await db.reconciliations.insert_one(report.model_dump())
    return report

@router.get("/reconciliation", response_model=List[ReconciliationReport])
async def get_reconciliations():
    db = get_db()
    reports = await db.reconciliations.find().sort("created_at", -1).limit(20).to_list(20)
    return [ReconciliationReport(**r) for r in reports]

# --- SCHEDULER ---

@router.get("/reconciliation/config", response_model=List[ReconciliationSchedule])
async def get_recon_config():
    db = get_db()
    configs = await db.recon_schedules.find().to_list(100)
    if not configs:
        # Seed default
        def_conf = ReconciliationSchedule(provider="Stripe", frequency="daily")
        await db.recon_schedules.insert_one(def_conf.model_dump())
        return [def_conf]
    return [ReconciliationSchedule(**c) for c in configs]

@router.post("/reconciliation/config")
async def update_recon_config(config: ReconciliationSchedule):
    db = get_db()
    await db.recon_schedules.update_one(
        {"provider": config.provider}, 
        {"$set": config.model_dump()}, 
        upsert=True
    )
    return {"message": "Schedule updated"}

@router.post("/reconciliation/run-auto")
async def run_auto_reconciliation(provider: str = Body(..., embed=True)):
    # Mock Auto Run
    report = ReconciliationReport(
        provider_name=provider,
        file_name=f"Auto-Fetch-{datetime.now().strftime('%Y%m%d-%H%M')}",
        status="completed",
        period_start=datetime.now(timezone.utc),
        period_end=datetime.now(timezone.utc),
        total_records=150,
        mismatches=2
    )
    db = get_db()
    await db.reconciliations.insert_one(report.model_dump())
    return report

# --- CHARGEBACKS ---

@router.get("/chargebacks", response_model=List[ChargebackCase])
async def get_chargebacks():
    db = get_db()
    cases = await db.chargebacks.find().sort("created_at", -1).limit(50).to_list(50)
    return [ChargebackCase(**c) for c in cases]

@router.post("/chargebacks")
async def create_chargeback(case: ChargebackCase):
    db = get_db()
    
    # Enrich with Risk Score from TX
    tx = await db.transactions.find_one({"id": case.transaction_id})
    if tx:
        risk_level = tx.get("risk_score_at_time", "low")
        score_map = {"low": 10, "medium": 50, "high": 80, "critical": 95}
        case.risk_score_at_time = score_map.get(risk_level, 0)
        
        # Cluster Check
        if case.risk_score_at_time > 70:
            case.fraud_cluster_id = f"cluster_{random.randint(1000,9999)}"

    await db.chargebacks.insert_one(case.model_dump())
    
    # Audit Log
    await db.audit_logs.insert_one(AuditLogEntry(
        admin_id="current_admin",
        action="create_chargeback",
        target_id=case.id,
        target_type="chargeback",
        details=f"Created case for TX {case.transaction_id}"
    ).model_dump())
    
    return case

@router.post("/chargebacks/{case_id}/evidence")
async def upload_evidence(case_id: str, file_url: str = Body(..., embed=True)):
    db = get_db()
    await db.chargebacks.update_one(
        {"id": case_id}, 
        {
            "$push": {"evidence_files": file_url},
            "$set": {"status": ChargebackStatus.EVIDENCE_GATHERING}
        }
    )
    return {"message": "Evidence uploaded"}

# --- ROUTING ---

@router.get("/routing/rules")
async def get_routing_rules():
    return [
        {"id": "rule_1", "name": "High Risk -> Crypto Only", "condition": "risk_score > 80", "action": "route_to_crypto"},
        {"id": "rule_2", "name": "TR Traffic -> Papara", "condition": "country == 'TR'", "action": "route_to_papara"},
        {"id": "rule_3", "name": "Failover Stripe -> Adyen", "condition": "gateway_error == 'stripe_down'", "action": "route_to_adyen"},
    ]
