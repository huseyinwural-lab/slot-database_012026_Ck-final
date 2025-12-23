import asyncio
from app.core.database import async_session
from app.models.sql_models import Transaction
from sqlmodel import select

async def check():
    async with async_session() as session:
        result = await session.execute(select(Transaction).where(Transaction.provider == "stripe"))
        txs = result.scalars().all()
        print(f"Found {len(txs)} Stripe transactions")
        for tx in txs:
            print(f"ID: {tx.id}, Status: {tx.status}, State: {tx.state}, ProviderID: {tx.provider_event_id}, Amount: {tx.amount}")

if __name__ == "__main__":
    asyncio.run(check())