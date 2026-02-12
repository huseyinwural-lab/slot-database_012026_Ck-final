import sys
import os
# Adjust path
sys.path.append("/app/backend")

from app.services.providers.registry import ProviderRegistry
from app.services.providers.adapters import PragmaticAdapter

def test_registry():
    print("--- Testing Provider Registry ---")
    
    try:
        adapter = ProviderRegistry.get_adapter("pragmatic")
        assert isinstance(adapter, PragmaticAdapter)
        print("✅ Pragmatic adapter loaded")
        
        req = {"userId": "p1", "amount": 100, "currency": "USD"}
        mapped = adapter.map_request(req)
        assert mapped["player_id"] == "p1"
        assert mapped["amount"] == 100.0
        print("✅ Request mapping verified")
        
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_registry()
