from fastapi import APIRouter, HTTPException, UploadFile, File, Body
from typing import List, Optional
from datetime import datetime, timezone
import csv
import io
from app.models.finance import ReconciliationReport, ReconciliationItem, ChargebackCase, ChargebackStatus, AuditLogEntry
from app.models.core import Transaction
from config import settings
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter(prefix="/api/v1/finance", tags=["finance_advanced"])

def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# --- RECONCILIATION ---

@router.post("/reconciliation/upload", response_model=ReconciliationReport)
async def upload_reconciliation(
    provider: str, 
    file: UploadFile = File(...)
):
    db = get_db()
    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    
    report = ReconciliationReport(
        provider_name=provider,
        file_name=file.filename,
        period_start=datetime.now(timezone.utc), # Mock
        period_end=datetime.now(timezone.utc)
    )
    
    items = []
    # Mock Processing Logic
    for row in reader:
        # Assuming CSV has 'tx_id', 'amount'
        ref_id = row.get('tx_id', 'unknown')
        amount = float(row.get('amount', 0))
        
        # Check DB
        tx = await db.transactions.find_one({"provider_tx_id": ref_id})
        
        if not tx:
            items.append(ReconciliationItem(
                provider_ref=ref_id, 
                provider_amount=amount, 
                status="missing_in_db",
                difference=amount
            ))
        elif abs(tx['amount'] - amount) > 0.01:
            items.append(ReconciliationItem(
                transaction_id=tx['id'],
                provider_ref=ref_id,
                db_amount=tx['amount'],
                provider_amount=amount,
                status="mismatch_amount",
                difference=tx['amount'] - amount
            ))
        else:
            items.append(ReconciliationItem(
                transaction_id=tx['id'],
                provider_ref=ref_id,
                db_amount=tx['amount'],
                provider_amount=amount,
                status="matched"
            ))
            
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

# --- CHARGEBACKS ---

@router.get("/chargebacks", response_model=List[ChargebackCase])
async def get_chargebacks():
    db = get_db()
    cases = await db.chargebacks.find().sort("created_at", -1).limit(50).to_list(50)
    return [ChargebackCase(**c) for c in cases]

@router.post("/chargebacks")
async def create_chargeback(case: ChargebackCase):
    db = get_db()
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

# --- ROUTING (Simple Rule Engine) ---

@router.get("/routing/rules")
async def get_routing_rules():
    return [
        {"id": "rule_1", "name": "High Risk -> Crypto Only", "condition": "risk_score > 80", "action": "route_to_crypto"},
        {"id": "rule_2", "name": "TR Traffic -> Papara", "condition": "country == 'TR'", "action": "route_to_papara"},
        {"id": "rule_3", "name": "Failover Stripe -> Adyen", "condition": "gateway_error == 'stripe_down'", "action": "route_to_adyen"},
    ]
