from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.payment_analytics_models import RoutingRule
from app.services.payments.routing.router import PaymentRouter as BaseRouter # Extend V1

class SmartRouter(BaseRouter):
    async def get_smart_route(
        self, 
        session: AsyncSession,
        tenant_id: str, 
        currency: str, 
        country: str,
        method: str
    ) -> List[str]:
        
        # 1. Check DB Rules
        stmt = select(RoutingRule).where(
            (RoutingRule.tenant_id == tenant_id) | (RoutingRule.tenant_id == None),
            (RoutingRule.currency == currency) | (RoutingRule.currency == None),
            (RoutingRule.country == country) | (RoutingRule.country == None),
            (RoutingRule.method == method) | (RoutingRule.method == None)
        ).order_by(RoutingRule.tenant_id.desc(), RoutingRule.country.desc()) # Specific first
        
        rules = (await session.execute(stmt)).scalars().all()
        
        if rules:
            # Return priority from most specific rule
            return rules[0].provider_priority
            
        # 2. Fallback to Score-based (Simulated here, normally Redis/DB stats)
        # Mock Logic: Prefer Stripe for USD, Adyen for EUR
        if currency == "EUR":
            return ["adyen_mock", "stripe_mock"]
            
        # 3. Default V1
        return ["stripe_mock", "adyen_mock"]
