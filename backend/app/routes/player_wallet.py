from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.models.sql_models import Transaction, Player
from app.core.database import get_session
from app.utils.auth_player import get_current_player
from app.models.common import PaginatedResponse

router = APIRouter(prefix="/api/v1/player/wallet", tags=["player_wallet"])

@router.get("/balance")
async def get_balance(
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session)
):
    """Get current player balance"""
    # Force refresh from DB
    await session.refresh(current_player)
    return {
        "balance_real": current_player.balance_real,
        "balance_bonus": current_player.balance_bonus,
        "currency": "USD"
    }

@router.post("/deposit")
async def create_deposit(
    amount: float = Body(..., embed=True),
    method: str = Body(..., embed=True),
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session)
):
    if amount <= 0:
        raise HTTPException(400, "Amount must be positive")
        
    tx_id = str(uuid.uuid4())
    
    tx = Transaction(
        id=tx_id,
        tenant_id=current_player.tenant_id,
        player_id=current_player.id,
        type="deposit",
        amount=amount,
        status="completed",
        method=method,
        provider_tx_id="MockGateway",
        balance_after=current_player.balance_real + amount
    )
    
    session.add(tx)
    
    # Update Player Balance
    current_player.balance_real += amount
    session.add(current_player)
    
    await session.commit()
    await session.refresh(tx)
    
    return {"message": "Deposit successful", "transaction_id": tx_id, "new_balance": tx.balance_after}

@router.post("/withdraw")
async def create_withdrawal(
    amount: float = Body(..., embed=True),
    method: str = Body(..., embed=True),
    address: str = Body(..., embed=True),
    current_player: Player = Depends(get_current_player),
    session: AsyncSession = Depends(get_session)
):
    if amount <= 0:
        raise HTTPException(400, "Amount must be positive")
        
    # Refresh to ensure balance check is accurate
    await session.refresh(current_player)
    
    if current_player.balance_real < amount:
        raise HTTPException(400, "Insufficient funds")
        
    tx_id = str(uuid.uuid4())
    
    tx = Transaction(
        id=tx_id,
        tenant_id=current_player.tenant_id,
        player_id=current_player.id,
        type="withdrawal",
        amount=amount,
        status="pending",
        method=method,
        balance_after=current_player.balance_real - amount
    )
    
    session.add(tx)
    
    # Deduct Balance
    current_player.balance_real -= amount
    session.add(current_player)
    
    await session.commit()
    
    return {"message": "Withdrawal requested successfully", "transaction_id": tx_id}

@router.get("/transactions", response_model=PaginatedResponse[Transaction])
async def get_my_transactions(
    current_player: Player = Depends(get_current_player),
    page: int = 1,
    limit: int = 20,
    session: AsyncSession = Depends(get_session)
):
    skip = (page - 1) * limit
    
    query = select(Transaction).where(Transaction.player_id == current_player.id).order_by(Transaction.created_at.desc())
    
    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0
    
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "meta": {"total": total, "page": page, "page_size": limit}
    }
