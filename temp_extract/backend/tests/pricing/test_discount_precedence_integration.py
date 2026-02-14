import pytest
import pytest_asyncio
from datetime import datetime
from decimal import Decimal
from sqlmodel import delete
from app.pricing.discount_resolver import DiscountResolver
from app.models.discount import Discount, DiscountRules, DiscountTypeEnum, SegmentTypeEnum

@pytest_asyncio.fixture
async def db_session(async_session_factory):
    async with async_session_factory() as session:
        # Cleanup before yielding
        await session.execute(delete(DiscountRules))
        await session.execute(delete(Discount))
        await session.commit()
        yield session
        # Cleanup after
        await session.execute(delete(DiscountRules))
        await session.execute(delete(Discount))
        await session.commit()

@pytest.mark.asyncio
async def test_manual_override_wins(db_session):
    # Setup
    now = datetime.utcnow()
    
    d1 = Discount(code="D1", type=DiscountTypeEnum.FLAT, value=10, start_at=now)
    d2 = Discount(code="D2", type=DiscountTypeEnum.FLAT, value=20, start_at=now)
    d3 = Discount(code="D3", type=DiscountTypeEnum.FLAT, value=5, start_at=now)
    db_session.add_all([d1, d2, d3])
    await db_session.commit()
    await db_session.refresh(d1)
    await db_session.refresh(d2)
    await db_session.refresh(d3)

    r1 = DiscountRules(discount_id=d1.id, priority=10, tenant_id="t1") # Segment Default
    r2 = DiscountRules(discount_id=d2.id, priority=50, tenant_id="t1") # Campaign
    r3 = DiscountRules(discount_id=d3.id, priority=100, tenant_id="t1") # Manual
    db_session.add_all([r1, r2, r3])
    await db_session.commit()

    resolver = DiscountResolver(db_session)
    context = {'tenant_id': "t1", 'now': now}
    
    applied = await resolver.resolve(context, Decimal(100))
    
    assert applied is not None
    assert applied.code == "D3" # Manual override wins (priority 100)
    
    final, amount = resolver.calculate_final_price(Decimal(100), applied)
    assert final == 95
    assert amount == 5

@pytest.mark.asyncio
async def test_campaign_beats_segment(db_session):
    now = datetime.utcnow()
    d1 = Discount(code="D1_T2", type=DiscountTypeEnum.PERCENTAGE, value=20, start_at=now)
    d2 = Discount(code="D2_T2", type=DiscountTypeEnum.PERCENTAGE, value=30, start_at=now)
    db_session.add_all([d1, d2])
    await db_session.commit()
    await db_session.refresh(d1); await db_session.refresh(d2)

    r1 = DiscountRules(discount_id=d1.id, priority=10, tenant_id="t1") # Dealer Rate
    r2 = DiscountRules(discount_id=d2.id, priority=20, tenant_id="t1") # Summer Sale
    db_session.add_all([r1, r2])
    await db_session.commit()
    
    resolver = DiscountResolver(db_session)
    context = {'tenant_id': "t1", 'now': now}
    
    applied = await resolver.resolve(context, Decimal(100))
    
    assert applied.code == "D2_T2"
    
    final, amount = resolver.calculate_final_price(Decimal(100), applied)
    assert final == 70 # 100 - 30%
