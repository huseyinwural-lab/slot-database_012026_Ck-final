import pytest
from unittest.mock import MagicMock
from app.pricing.service_integration_snippet import PricingService
from app.models import User
from app.pricing.segment_resolver import SegmentType

@pytest.fixture
def mock_service():
    service = PricingService()
    service.user_repo = MagicMock()
    service.quota_service = MagicMock()
    service.package_service = MagicMock()
    service.rate_service = MagicMock()
    return service

def test_individual_hits_limit_goes_paid(mock_service):
    # User is Individual
    user = User(id=1, segment_type=SegmentType.INDIVIDUAL)
    mock_service.user_repo.get.return_value = user
    
    # Used 3 (Limit is 3)
    mock_service.quota_service.get_usage.return_value = 3
    
    # Base Rate 100
    mock_service.rate_service.get_base_rate.return_value = 100.0
    
    quote = mock_service.calculate_quote(1, "standard")
    
    # Should skip package (no access) and go paid
    assert quote.type == "PAID"
    assert quote.price == 100.0

def test_dealer_uses_package(mock_service):
    # User is Dealer
    user = User(id=2, segment_type=SegmentType.DEALER)
    mock_service.user_repo.get.return_value = user
    
    # Used 50 (Limit 50) -> Free exhausted
    mock_service.quota_service.get_usage.return_value = 50
    
    # Has Package Credits
    mock_service.package_service.has_credits.return_value = True
    
    quote = mock_service.calculate_quote(2, "standard")
    
    assert quote.type == "PACKAGE"
    assert quote.price == 0

def test_dealer_paid_discount(mock_service):
    # User is Dealer
    user = User(id=3, segment_type=SegmentType.DEALER)
    mock_service.user_repo.get.return_value = user
    
    # Free exhausted, No Package
    mock_service.quota_service.get_usage.return_value = 50
    mock_service.package_service.has_credits.return_value = False
    
    # Base Rate 100
    mock_service.rate_service.get_base_rate.return_value = 100.0
    
    quote = mock_service.calculate_quote(3, "standard")
    
    assert quote.type == "PAID"
    assert quote.price == 80.0 # 20% discount applied
