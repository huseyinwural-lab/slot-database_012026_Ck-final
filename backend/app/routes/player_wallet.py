from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.models.core import Transaction, TransactionType, TransactionStatus
from app.core.database import db_wrapper
from app.utils.auth_player import get_current_player
from app.models.common import PaginatedResponse

router = APIRouter(prefix="/api/v1/player/wallet", tags=["player_wallet"])

@router.get("/balance")
async def get_balance(current_player: dict = Depends(get_current_player)):
    """Get current player balance"""
    db = db_wrapper.db
    player = await db.players.find_one({"id": current_player["id"]})
    if not player:
        raise HTTPException(404, "Player not found")
        
    return {
        "balance_real": player.get("balance_real", 0.0),
        "balance_bonus": player.get("balance_bonus", 0.0),
        "currency": "USD" # Mock currency
    }

@router.post("/deposit")
async def create_deposit(
    amount: float = Body(..., embed=True),
    method: str = Body(..., embed=True),
    current_player: dict = Depends(get_current_player)
):
    """
    Simulate a deposit. 
    In a real app, this would redirect to a payment gateway.
    For this MVP, we auto-complete it for testing.
    """
    if amount <= 0:
        raise HTTPException(400, "Amount must be positive")
        
    db = db_wrapper.db
    
    tx_id = str(uuid.uuid4())
    
    tx = Transaction(
        id=tx_id,
        tenant_id=current_player["tenant_id"],
        player_id=current_player["id"],
        player_username=current_player["username"],
        type=TransactionType.DEPOSIT,
        amount=amount,
        status=TransactionStatus.COMPLETED, # Auto-complete for MVP
        method=method,
        provider="MockGateway",
        balance_after=current_player.get("balance_real", 0.0) + amount, # Approx
        description=f"Deposit via {method}"
    )
    
    # Insert TX
    await db.transactions.insert_one(tx.model_dump())
    
    # Update Player Balance
    await db.players.update_one(
        {"id": current_player["id"]},
        {"$inc": {"balance_real": amount, "total_deposits": amount}}
    )
    
    return {"message": "Deposit successful", "transaction_id": tx_id, "new_balance": tx.balance_after}

@router.post("/withdraw")
async def create_withdrawal(
    amount: float = Body(..., embed=True),
    method: str = Body(..., embed=True),
    address: str = Body(..., embed=True),
    current_player: dict = Depends(get_current_player)
):
    """
    Request a withdrawal.
    This goes to 'pending' status for Admin approval.
    """
    if amount <= 0:
        raise HTTPException(400, "Amount must be positive")
        
    db = db_wrapper.db
    
    # Check balance
    player = await db.players.find_one({"id": current_player["id"]})
    if player.get("balance_real", 0.0) < amount:
        raise HTTPException(400, "Insufficient funds")
        
    tx_id = str(uuid.uuid4())
    
    tx = Transaction(
        id=tx_id,
        tenant_id=current_player["tenant_id"],
        player_id=current_player["id"],
        player_username=current_player["username"],
        type=TransactionType.WITHDRAWAL,
        amount=amount,
        status=TransactionStatus.PENDING, # Needs approval
        method=method,
        destination_address=address,
        provider="Internal",
        balance_after=player.get("balance_real", 0.0) - amount
    )
    
    # Insert TX
    await db.transactions.insert_one(tx.model_dump())
    
    # Deduct Balance immediately (lock funds)
    await db.players.update_one(
        {"id": current_player["id"]},
        {
            "$inc": {"balance_real": -amount, "pending_withdrawals": amount}
        }
    )
    
    return {"message": "Withdrawal requested successfully", "transaction_id": tx_id}

@router.get("/transactions", response_model=PaginatedResponse[Transaction])
async def get_my_transactions(
    current_player: dict = Depends(get_current_player),
    page: int = 1,
    limit: int = 20
):
    db = db_wrapper.db
    skip = (page - 1) * limit
    
    query = {"player_id": current_player["id"]}
    
    cursor = db.transactions.find(query).sort("created_at", -1).skip(skip).limit(limit)
    items = await cursor.to_list(limit)
    total = await db.transactions.count_documents(query)
    
    return {
        "items": [Transaction(**t) for t in items],
        "meta": {"total": total, "page": page, "page_size": limit}
    }
