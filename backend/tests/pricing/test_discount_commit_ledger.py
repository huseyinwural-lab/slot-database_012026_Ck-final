import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from datetime import datetime
from app.pricing.service import PricingService, Quote
from app.pricing.models.discount import DiscountType

# Mock Ledger Service
@pytest.fixture
def mock_ledger():
    return MagicMock()

def test_ledger_commit_with_discount(mock_ledger):
    # Setup
    service = PricingService(ledger=mock_ledger)
    quote = Quote(
        price=Decimal(80),
        type="PAID",
        details={
            "gross_amount": Decimal(100),
            "discount_amount": Decimal(20),
            "discount_id": "d1"
        }
    )
    
    # Act
    service.commit_transaction(tenant_id="t1", listing_id="l1", quote=quote)
    
    # Assert
    mock_ledger.record.assert_called_once()
    args = mock_ledger.record.call_args[1]
    assert args['amount'] == Decimal(80)
    assert args['gross_amount'] == Decimal(100)
    assert args['discount_amount'] == Decimal(20)
    assert args['applied_discount_id'] == "d1"

def test_ledger_commit_free_no_discount(mock_ledger):
    # Setup
    service = PricingService(ledger=mock_ledger)
    quote = Quote(price=Decimal(0), type="FREE")
    
    # Act
    service.commit_transaction(tenant_id="t1", listing_id="l1", quote=quote)
    
    # Assert
    args = mock_ledger.record.call_args[1]
    assert args['amount'] == 0
    assert args['gross_amount'] == 0
    assert args['discount_amount'] == 0
    assert args['applied_discount_id'] is None
