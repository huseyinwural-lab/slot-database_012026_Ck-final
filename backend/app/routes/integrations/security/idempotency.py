from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.sql_models import Transaction

async def check_idempotency(session: AsyncSession, idempotency_key: str):
    """
    Check if a transaction with the given idempotency key already exists.
    Returns existing transaction or None.
    """
    if not idempotency_key:
        return None
        
    stmt = select(Transaction).where(Transaction.idempotency_key == idempotency_key)
    existing = (await session.execute(stmt)).scalars().first()
    return existing

async def enforce_idempotency(session: AsyncSession, idempotency_key: str):
    """
    Raise 409 if exists (or handle as success return depending on contract).
    For Provider Contract v1, we return success with existing ref if found (idempotent success).
    """
    existing = await check_idempotency(session, idempotency_key)
    if existing:
        # Contract: Return success with existing ref data
        # We raise a special exception or return the object to be handled by the route
        return existing
    return None
