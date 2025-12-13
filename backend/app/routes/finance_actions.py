from fastapi import APIRouter, HTTPException, Body, Depends
from datetime import datetime, timezone
from app.models.core import Transaction, TransactionStatus
from app.utils.auth import get_current_admin
from app.models.domain.admin import AdminUser
from app.core.database import db_wrapper

router = APIRouter()

@router.post("/finance/transactions/{tx_id}/action")
async def action_transaction(
    tx_id: str, 
    action: str = Body(..., embed=True), 
    reason: str = Body(None, embed=True),
    payment_method: str = Body(None, embed=True),
    current_admin: AdminUser = Depends(get_current_admin)
):
    db = db_wrapper.db
    tx = await db.transactions.find_one({"id": tx_id})
    if not tx:
        raise HTTPException(404, "Transaction not found")
        
    # Tenant check
    if not current_admin.is_platform_owner and tx.get("tenant_id") != current_admin.tenant_id:
        raise HTTPException(403, "Access denied")

    new_status = None
    if action == "approve":
        new_status = TransactionStatus.COMPLETED
    elif action == "reject":
        new_status = TransactionStatus.REJECTED
    elif action == "pending_review":
        new_status = TransactionStatus.PENDING_REVIEW
    elif action == "add_note":
        pass # Just adding note
    else:
        raise HTTPException(400, "Invalid action")

    update_fields = {
        "updated_at": datetime.now(timezone.utc)
    }
    
    if new_status:
        update_fields["status"] = new_status
        if payment_method:
            update_fields["payment_method_executed"] = payment_method
            
    await db.transactions.update_one(
        {"id": tx_id},
        {
            "$set": update_fields,
            "$push": {
                "timeline": {
                    "status": action,
                    "description": reason,
                    "timestamp": datetime.now(timezone.utc),
                    "operator": current_admin.email
                }
            }
        }
    )
    
    return {"message": f"Transaction {action} successful"}
