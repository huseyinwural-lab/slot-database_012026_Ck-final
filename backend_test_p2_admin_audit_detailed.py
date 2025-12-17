#!/usr/bin/env python3
"""
P2 Backlog #2 - Admin Change Audit Events Detailed PII Redaction Testing
Specifically testing email PII redaction in audit events
"""

import requests
import json
import sys
import os
import time
import uuid
import re
import hashlib
from typing import Dict, Any, Optional

# Configuration - Use frontend .env for external URL
BASE_URL = "https://game-admin-hub-1.preview.emergentagent.com"  # Default
try:
    with open("/app/frontend/.env", "r") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
except FileNotFoundError:
    pass

API_BASE = f"{BASE_URL}/api"

def make_request(method: str, endpoint: str, headers: Dict = None, json_data: Dict = None) -> Dict[str, Any]:
    """Make HTTP request and return response details"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=json_data, timeout=30)
        elif method.upper() == "PATCH":
            response = requests.patch(url, headers=headers, json=json_data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        try:
            response_json = response.json()
        except:
            response_json = {"raw_text": response.text}
        
        return {
            "status_code": response.status_code,
            "json": response_json,
            "headers": dict(response.headers)
        }
    except Exception as e:
        return {
            "status_code": 0,
            "json": {"error": str(e)},
            "headers": {}
        }

def main():
    print("=== P2 ADMIN AUDIT EVENTS DETAILED PII REDACTION TEST ===")
    print(f"Testing against: {BASE_URL}")
    
    # Login as owner
    login_data = {
        "email": "admin@casino.com",
        "password": "Admin123!"
    }
    
    response = make_request("POST", "/v1/auth/login", json_data=login_data)
    if response["status_code"] != 200:
        print(f"❌ Login failed: {response['status_code']}")
        return False
    
    token = response["json"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Owner login successful")
    
    # Create a test admin user
    test_email = f"detailed.test.{int(time.time())}@casino.com"
    admin_data = {
        "email": test_email,
        "full_name": "Detailed Test Admin",
        "role": "Admin",
        "password_mode": "invite",
        "tenant_id": "default_casino"
    }
    
    response = make_request("POST", "/v1/admin/users", headers=headers, json_data=admin_data)
    if response["status_code"] != 200:
        print(f"❌ Admin creation failed: {response['status_code']}")
        return False
    
    # Get admin ID
    list_response = make_request("GET", "/v1/admin/users", headers=headers)
    admins = list_response["json"]
    admin_id = None
    for admin in admins:
        if admin.get("email") == test_email:
            admin_id = admin["id"]
            break
    
    if not admin_id:
        print("❌ Cannot find created admin")
        return False
    
    print(f"✅ Admin created with ID: {admin_id}")
    
    # Update email to trigger PII redaction
    new_email = f"detailed.updated.{int(time.time())}@casino.com"
    update_data = {
        "email": new_email,
        "full_name": "Updated Detailed Test Admin"
    }
    
    print(f"📧 Updating email from {test_email} to {new_email}")
    
    response = make_request("PATCH", f"/v1/admin/users/{admin_id}", headers=headers, json_data=update_data)
    if response["status_code"] != 200:
        print(f"❌ Email update failed: {response['status_code']}")
        return False
    
    print("✅ Email update successful")
    
    # Wait for audit event
    time.sleep(2)
    
    # Query for the specific admin.user_updated event
    response = make_request("GET", "/v1/audit/events?action=admin.user_updated&since_hours=1&limit=20", headers=headers)
    if response["status_code"] != 200:
        print(f"❌ Cannot fetch audit events: {response['status_code']}")
        return False
    
    events = response["json"].get("items", [])
    
    # Find the event for our admin
    target_event = None
    for event in events:
        if event.get("resource_id") == admin_id:
            target_event = event
            break
    
    if not target_event:
        print("❌ Cannot find audit event for our admin update")
        return False
    
    print(f"✅ Found audit event: {target_event.get('id')}")
    
    # Detailed analysis of the audit event
    print("\n=== DETAILED AUDIT EVENT ANALYSIS ===")
    
    details = target_event.get("details", {})
    changed = details.get("changed", {})
    
    print(f"Event ID: {target_event.get('id')}")
    print(f"Action: {target_event.get('action')}")
    print(f"Resource Type: {target_event.get('resource_type')}")
    print(f"Resource ID: {target_event.get('resource_id')}")
    print(f"Result: {target_event.get('result')}")
    print(f"Timestamp: {target_event.get('timestamp')}")
    print(f"Actor User ID: {target_event.get('actor_user_id')}")
    print(f"Tenant ID: {target_event.get('tenant_id')}")
    print(f"IP Address: {target_event.get('ip_address')}")
    print(f"Request ID: {target_event.get('request_id')}")
    
    print(f"\nChanged fields: {list(changed.keys())}")
    
    # Check email redaction
    if "email" in changed:
        email_change = changed["email"]
        print(f"\nEmail change structure: {json.dumps(email_change, indent=2)}")
        
        if isinstance(email_change, dict):
            if "changed" in email_change and email_change["changed"] is True:
                if "before_hash" in email_change and "after_hash" in email_change:
                    before_hash = email_change["before_hash"]
                    after_hash = email_change["after_hash"]
                    
                    print(f"✅ Email properly redacted:")
                    print(f"   Before hash: {before_hash}")
                    print(f"   After hash: {after_hash}")
                    
                    # Verify hash format
                    if re.match(r'^[a-f0-9]{64}$', before_hash) and re.match(r'^[a-f0-9]{64}$', after_hash):
                        print("✅ Hash format is correct (64 hex chars)")
                    else:
                        print("❌ Hash format is incorrect")
                        return False
                    
                    # Verify no raw email in the entire event
                    event_str = json.dumps(target_event).lower()
                    if test_email.lower() in event_str or new_email.lower() in event_str:
                        print("❌ Raw email found in audit event!")
                        print(f"Event JSON: {json.dumps(target_event, indent=2)}")
                        return False
                    else:
                        print("✅ No raw email found in audit event")
                else:
                    print("❌ Email change missing hash fields")
                    return False
            else:
                print("❌ Email change structure invalid")
                return False
        else:
            print("❌ Email change is not a dict")
            return False
    else:
        print("❌ No email change found in audit event")
        return False
    
    # Check full_name (safe field)
    if "full_name" in changed:
        full_name_change = changed["full_name"]
        print(f"\nFull name change structure: {json.dumps(full_name_change, indent=2)}")
        
        if isinstance(full_name_change, dict) and "before" in full_name_change and "after" in full_name_change:
            print("✅ Full name contains raw before/after values (safe field)")
        else:
            print("❌ Full name change structure invalid")
            return False
    
    # Check for sensitive data leakage
    sensitive_terms = ["password", "token", "authorization", "cookie", "secret", "admin123"]
    event_str = json.dumps(target_event).lower()
    leaked_terms = [term for term in sensitive_terms if term in event_str]
    
    if leaked_terms:
        print(f"❌ Sensitive data leaked: {leaked_terms}")
        return False
    else:
        print("✅ No sensitive data found in audit event")
    
    print("\n🎉 ALL DETAILED PII REDACTION TESTS PASSED!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)