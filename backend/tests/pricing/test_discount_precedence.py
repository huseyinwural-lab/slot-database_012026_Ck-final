import pytest
from decimal import Decimal
from app.pricing.discount_resolver import DiscountResolver, DiscountRule

# Test-First: Precedence Logic

def test_manual_override_wins():
    """Manual override should beat campaign and segment defaults."""
    rules = [
        DiscountRule(name="Segment Default", priority=10, amount=10),
        DiscountRule(name="Black Friday", priority=50, amount=20),
        DiscountRule(name="Manual Admin", priority=100, amount=5) 
        # Even if amount is lower? Policy says priority wins.
        # Decision: Priority determines 'applicability', not 'best price' in this model.
    ]
    
    resolver = DiscountResolver(rules)
    applied = resolver.resolve(base_price=100)
    
    assert applied.name == "Manual Admin"
    assert applied.final_price == 95

def test_campaign_beats_segment():
    """Campaign should override standard segment pricing."""
    rules = [
        DiscountRule(name="Dealer Rate", priority=10, amount=Decimal("0.20"), type="PERCENT"),
        DiscountRule(name="Summer Sale", priority=20, amount=Decimal("0.30"), type="PERCENT")
    ]
    
    resolver = DiscountResolver(rules)
    applied = resolver.resolve(base_price=100)
    
    assert applied.name == "Summer Sale"
    assert applied.final_price == 70

def test_no_stacking():
    """Ensure discounts are NOT summed."""
    rules = [
        DiscountRule(name="A", priority=10, amount=10),
        DiscountRule(name="B", priority=10, amount=10)
    ]
    
    resolver = DiscountResolver(rules)
    applied = resolver.resolve(base_price=100)
    
    # Should apply only one (logic determinism needed for tie-break, e.g. newer first)
    assert applied.final_price == 90 # Not 80
