#!/usr/bin/env python3

import requests
import sys

def test_reconciliation_upload():
    """Test only the reconciliation upload endpoint"""
    
    base_url = "https://casino-finance-1.preview.emergentagent.com"
    
    # Create CSV content for testing
    csv_content = """tx_id,amount,currency
TX-001,100.50,USD
TX-002,250.75,EUR
TX-003,500.00,TRY
TX-MISSING-HIGH,7500.00,USD
TX-MISSING-LOW,25.50,EUR"""
    
    files = {
        'file': ('test_fx_reconciliation.csv', csv_content, 'text/csv')
    }
    
    url = f"{base_url}/api/v1/finance/reconciliation/upload?provider=Stripe"
    
    print(f"Testing Reconciliation Upload...")
    print(f"URL: {url}")
    
    try:
        response = requests.post(url, files=files, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response JSON: {data}")
                return True
            except Exception as e:
                print(f"JSON Parse Error: {e}")
                print(f"Raw Response: {response.text}")
                return False
        else:
            print(f"Error Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Request Error: {e}")
        return False

if __name__ == "__main__":
    success = test_reconciliation_upload()
    sys.exit(0 if success else 1)