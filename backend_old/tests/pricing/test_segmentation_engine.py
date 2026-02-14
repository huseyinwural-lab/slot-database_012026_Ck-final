import pytest
from app.pricing.engine import PricingEngine
from app.models import User, SegmentType

# Deterministic Test Suite for Segmentation

@pytest.fixture
def individual_user():
    return User(id=1, segment_type=SegmentType.INDIVIDUAL)

@pytest.fixture
def dealer_user():
    return User(id=2, segment_type=SegmentType.DEALER)

def test_individual_no_package_access(individual_user, pricing_engine):
    """Ensure INDIVIDUAL cannot use package logic even if credits exist (edge case)."""
    # Setup: Mock package credits (shouldn't happen in real life but possible via bug)
    pricing_engine.mock_package_credits(individual_user.id, 10)
    
    # Act
    quote = pricing_engine.calculate_quote(individual_user)
    
    # Assert
    assert quote.type != "PACKAGE"
    assert quote.type == "PAID" # Fallback to paid because free quota assumed full

def test_dealer_high_quota(dealer_user, pricing_engine):
    """Ensure DEALER gets higher free limits."""
    # Setup: Usage is 40 (Individual limit is 3, Dealer is 50)
    pricing_engine.mock_usage(dealer_user.id, 40)
    
    # Act
    quote = pricing_engine.calculate_quote(dealer_user)
    
    # Assert
    assert quote.type == "FREE" # 40 < 50

def test_downgrade_preserves_package(dealer_user, pricing_engine):
    """Downgraded users should still consume existing package credits."""
    # Setup: Dealer buys package
    pricing_engine.mock_package_credits(dealer_user.id, 5)
    
    # Act: Downgrade
    dealer_user.segment_type = SegmentType.INDIVIDUAL
    
    # Act: Quote
    quote = pricing_engine.calculate_quote(dealer_user)
    
    # Assert
    # Per Decision 3: Rights are preserved
    assert quote.type == "PACKAGE" 
