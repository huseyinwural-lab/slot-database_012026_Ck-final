import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from datetime import datetime
from app.pricing.discount_resolver import DiscountResolver, AppliedDiscount
from app.pricing.models.discount import Discount, DiscountRule, DiscountType

# Mock DB Session not needed for logic tests if we mock the query result, 
# but let's test the calculation logic directly first.

def test_calculate_final_price_percentage():
    resolver = DiscountResolver(MagicMock())
    discount = AppliedDiscount(
        Discount(id="1", code="TEST", type=DiscountType.PERCENTAGE, value=Decimal(20), start_at=datetime.now()),
        DiscountRule(priority=10)
    )
    
    final, amount = resolver.calculate_final_price(Decimal(100), discount)
    assert final == 80
    assert amount == 20

def test_calculate_final_price_flat():
    resolver = DiscountResolver(MagicMock())
    discount = AppliedDiscount(
        Discount(id="1", code="TEST", type=DiscountType.FLAT, value=Decimal(15), start_at=datetime.now()),
        DiscountRule(priority=10)
    )
    
    final, amount = resolver.calculate_final_price(Decimal(100), discount)
    assert final == 85
    assert amount == 15

def test_abuse_guard_negative_price():
    resolver = DiscountResolver(MagicMock())
    discount = AppliedDiscount(
        Discount(id="1", code="TEST", type=DiscountType.FLAT, value=Decimal(150), start_at=datetime.now()),
        DiscountRule(priority=10)
    )
    
    # Base is 100, discount is 150. Price should be 0, not -50.
    final, amount = resolver.calculate_final_price(Decimal(100), discount)
    assert final == 0
    assert amount == 100 # Capped at base price
