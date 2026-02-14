import pytest
from unittest.mock import MagicMock, patch
from app.services.listing_service import ListingService

def test_listing_creation_rollback_on_pricing_fail():
    # Setup
    repo = MagicMock()
    pricing = MagicMock()
    service = ListingService(repo, pricing)
    
    # Pricing commit fails
    pricing.commit_transaction.side_effect = Exception("Ledger Error")
    
    # Act
    with pytest.raises(Exception, match="Ledger Error"):
        service.create_listing("t1", {})
        
    # Assert
    repo.save.assert_not_called() # Atomicity: Listing never saved if payment fails

def test_listing_creation_rollback_on_discount_error():
    # Setup
    pricing = MagicMock()
    pricing.calculate_quote.side_effect = Exception("Discount Resolver Error")
    service = ListingService(MagicMock(), pricing)
    
    # Act
    with pytest.raises(Exception, match="Discount Resolver Error"):
        service.create_listing("t1", {})
        
    # Assert: No side effects
