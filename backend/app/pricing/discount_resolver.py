from decimal import Decimal
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_
from app.pricing.models.discount import Discount, DiscountRule, DiscountType

class AppliedDiscount:
    def __init__(self, discount: Discount, rule: DiscountRule):
        self.id = discount.id
        self.code = discount.code
        self.type = discount.type
        self.value = discount.value
        self.priority = rule.priority

class DiscountResolver:
    def __init__(self, db: Session):
        self.db = db

    def resolve(self, user_context: dict, base_price: Decimal) -> Optional[AppliedDiscount]:
        """
        Finds the single best discount for the user based on precedence.
        User Context: { 'segment': 'INDIVIDUAL', 'tenant_id': 'uuid', 'now': datetime }
        """
        segment = user_context.get('segment')
        tenant_id = user_context.get('tenant_id')
        now = user_context.get('now', datetime.utcnow())

        # Query Rules that match the user profile
        # Join with Discount to check validity dates and active status
        stmt = (
            select(DiscountRule, Discount)
            .join(Discount)
            .where(
                Discount.is_active == True,
                Discount.start_at <= now,
                or_(Discount.end_at == None, Discount.end_at >= now),
                or_(
                    DiscountRule.segment_type == segment,
                    DiscountRule.tenant_id == tenant_id,
                    # We could add a 'global' rule here where both are null if business requires
                )
            )
            .order_by(DiscountRule.priority.desc()) # Highest priority wins (No Stacking)
            .limit(1) # Only 1 allowed
        )

        result = self.db.exec(stmt).first()

        if not result:
            return None

        rule, discount = result
        return AppliedDiscount(discount, rule)

    def calculate_final_price(self, base_price: Decimal, discount: Optional[AppliedDiscount]) -> tuple[Decimal, Decimal]:
        """Returns (Final Price, Discount Amount)"""
        if not discount:
            return base_price, Decimal(0)

        discount_amount = Decimal(0)
        
        if discount.type == DiscountType.FLAT:
            discount_amount = discount.value
        elif discount.type == DiscountType.PERCENTAGE:
            discount_amount = base_price * (discount.value / Decimal(100))

        # Abuse Guard: Negative Price Protection
        if discount_amount > base_price:
            discount_amount = base_price

        final_price = base_price - discount_amount
        return final_price, discount_amount
