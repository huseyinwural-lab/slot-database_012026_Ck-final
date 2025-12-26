#!/usr/bin/env python3

import requests
import sys
import json

def test_finance_endpoints():
    """Test finance endpoints individually"""
    
    base_url = "https://smart-robot-ui.preview.emergentagent.com"
    
    # Test 1: Auto-Scheduler Config
    print("1. Testing Auto-Scheduler Config...")
    config_data = {
        "provider": "TestProvider",
        "frequency": "hourly",
        "auto_fetch_enabled": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/finance/reconciliation/config", 
                               json=config_data, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Config update successful")
        else:
            print(f"   ❌ Config update failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Auto-Run Reconciliation
    print("\n2. Testing Auto-Run Reconciliation...")
    auto_run_data = {"provider": "TestProvider"}
    
    try:
        response = requests.post(f"{base_url}/api/v1/finance/reconciliation/run-auto", 
                               json=auto_run_data, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Auto-run successful: {data.get('provider_name', 'Unknown')}")
        else:
            print(f"   ❌ Auto-run failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Get Transactions for Chargeback Test
    print("\n3. Testing Get Transactions...")
    try:
        response = requests.get(f"{base_url}/api/v1/finance/transactions", timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            transactions = response.json()
            print(f"   ✅ Found {len(transactions)} transactions")
            return transactions[:1] if transactions else []
        else:
            print(f"   ❌ Failed to get transactions: {response.text}")
            return []
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []

def test_chargeback_creation(transactions):
    """Test chargeback creation with risk score integration"""
    
    base_url = "https://smart-robot-ui.preview.emergentagent.com"
    
    print("\n4. Testing Chargeback Creation...")
    
    if not transactions:
        print("   ⚠️  No transactions available, using mock data")
        chargeback_data = {
            "transaction_id": "TX-MOCK-001",
            "player_id": "player_mock",
            "amount": 1000.0,
            "reason_code": "4855",
            "due_date": "2025-02-15T00:00:00Z"
        }
    else:
        tx = transactions[0]
        chargeback_data = {
            "transaction_id": tx['id'],
            "player_id": tx.get('player_id', 'player_123'),
            "amount": 500.0,
            "reason_code": "4855",
            "due_date": "2025-02-15T00:00:00Z"
        }
    
    try:
        response = requests.post(f"{base_url}/api/v1/finance/chargebacks", 
                               json=chargeback_data, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Chargeback created: {data.get('id', 'Unknown')}")
            print(f"   📊 Risk Score: {data.get('risk_score_at_time', 'N/A')}")
            if data.get('fraud_cluster_id'):
                print(f"   🚨 Fraud Cluster: {data['fraud_cluster_id']}")
        else:
            print(f"   ❌ Chargeback creation failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_reconciliation_simple():
    """Test reconciliation endpoints without file upload"""
    
    base_url = "https://smart-robot-ui.preview.emergentagent.com"
    
    print("\n5. Testing Get Reconciliation Reports...")
    try:
        response = requests.get(f"{base_url}/api/v1/finance/reconciliation", timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            reports = response.json()
            print(f"   ✅ Found {len(reports)} reconciliation reports")
        else:
            print(f"   ❌ Failed to get reports: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n6. Testing Get Reconciliation Config...")
    try:
        response = requests.get(f"{base_url}/api/v1/finance/reconciliation/config", timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            configs = response.json()
            print(f"   ✅ Found {len(configs)} reconciliation configs")
        else:
            print(f"   ❌ Failed to get configs: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🎯 TESTING FINANCE ENDPOINTS (WITHOUT FILE UPLOAD)")
    print("=" * 60)
    
    transactions = test_finance_endpoints()
    test_chargeback_creation(transactions)
    test_reconciliation_simple()
    
    print("\n✅ Finance endpoint testing completed!")