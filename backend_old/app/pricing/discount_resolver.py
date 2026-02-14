from decimal import Decimal
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, or_, and_
from app.models.discount import Discount, DiscountRules, DiscountTypeEnum, SegmentTypeEnum

class AppliedDiscount:
    def __init__(self, discount: Discount, rule: DiscountRules):
        self.id = discount.id
        self.code = discount.code
        self.type = discount.type
        self.value = discount.value
        self.priority = rule.priority

class DiscountResolver:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def resolve(self, user_context: dict, base_price: Decimal) -> Optional[AppliedDiscount]:
        """
        Finds the single best discount for the user based on precedence.
        User Context: { 'segment': 'INDIVIDUAL', 'tenant_id': 'uuid', 'now': datetime }
        """
        segment = user_context.get('segment')
        tenant_id = user_context.get('tenant_id')
        now = user_context.get('now', datetime.utcnow())

        stmt = (
            select(DiscountRules, Discount)
            .join(Discount)
            .where(
                Discount.is_active == True,
                Discount.start_at <= now,
                or_(Discount.end_at == None, Discount.end_at >= now),
                or_(
                    DiscountRules.segment_type == segment,
                    DiscountRules.tenant_id == tenant_id,
                )
            )
            .order_by(DiscountRules.priority.desc()) # Highest priority wins
            .limit(1)
        )

        result = await self.db.execute(stmt)
        row = result.first()

        if not row:
            return None

        rule, discount = row
        return AppliedDiscount(discount, rule)

    def calculate_final_price(self, base_price: Decimal, discount: Optional[AppliedDiscount]) -> Tuple[Decimal, Decimal]:
        """Returns (Final Price, Discount Amount)"""
        if not discount:
            return Decimal(str(base_price)), Decimal(0)

        discount_amount = Decimal(0)
        base_price_dec = Decimal(str(base_price))
        value_dec = Decimal(str(discount.value))
        
        if discount.type == DiscountTypeEnum.FLAT:
            discount_amount = value_dec
        elif discount.type == DiscountTypeEnum.PERCENTAGE:
            discount_amount = base_price_dec * (value_dec / Decimal(100))

        # Abuse Guard: Negative Price Protection
        if discount_amount > base_price_dec:
            discount_amount = base_price_dec

        final_price = base_price_dec - discount_amount
        return final_price, discount_amount
