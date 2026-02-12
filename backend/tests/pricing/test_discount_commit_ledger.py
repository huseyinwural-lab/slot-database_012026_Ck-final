import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from app.pricing.service import PricingService
from app.pricing.schema import Quote

# Mock Ledger Service
@pytest.fixture
def mock_ledger():
    return MagicMock()

@pytest.mark.asyncio
async def test_ledger_commit_with_discount(mock_ledger):
    # Setup
    service = PricingService(None, None, None, None, ledger_service=mock_ledger)
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
    await service.commit_transaction(tenant_id="t1", listing_id="l1", quote=quote, player_id="p1")
    
    # Assert
    mock_ledger.record.assert_called_once()
    args = mock_ledger.record.call_args[1]
    assert args['amount'] == 80.0
    assert args['gross_amount'] == 100.0
    assert args['discount_amount'] == 20.0
    assert args['applied_discount_id'] == "d1"

@pytest.mark.asyncio
async def test_ledger_commit_free_no_discount(mock_ledger):
    # Setup
    service = PricingService(None, None, None, None, ledger_service=mock_ledger)
    quote = Quote(price=Decimal(0), type="FREE")
    
    # Act
    await service.commit_transaction(tenant_id="t1", listing_id="l1", quote=quote, player_id="p1")
    
    # Assert
    args = mock_ledger.record.call_args[1]
    assert args['amount'] == 0
    assert args['gross_amount'] == 0
    assert args['discount_amount'] == 0
    assert args['applied_discount_id'] is None
