#!/usr/bin/env python3
"""
Debug redaction in audit events
"""

import requests
import json
import uuid

# Configuration
try:
    with open("/app/frontend/.env", "r") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
        else:
            BASE_URL = "https://cash-flow-319.preview.emergentagent.com"
except:
    BASE_URL = "https://cash-flow-319.preview.emergentagent.com"

API_BASE = f"{BASE_URL}/api"

def make_request(method: str, endpoint: str, headers=None, json_data=None):
    """Make HTTP request and return response details"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=json_data, timeout=30)
        
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
    # Login first
    login_data = {
        "email": "admin@casino.com",
        "password": "Admin123!"
    }
    
    response = make_request("POST", "/v1/auth/login", json_data=login_data)
    if response["status_code"] != 200:
        print("Login failed")
        return
    
    token = response["json"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get recent audit events
    response = make_request("GET", "/v1/audit/events?since_hours=1&limit=20", headers=headers)
    
    if response["status_code"] == 200:
        items = response["json"]["items"]
        print(f"Found {len(items)} audit events")
        
        for i, item in enumerate(items):
            print(f"\n--- Event {i+1} ---")
            print(f"Action: {item.get('action')}")
            print(f"Resource Type: {item.get('resource_type')}")
            print(f"Details: {json.dumps(item.get('details', {}), indent=2)}")
            
            # Check for sensitive keys
            details = item.get("details", {})
            if isinstance(details, dict):
                for key, value in details.items():
                    if key.lower() in ["password", "token", "secret", "api_key"]:
                        print(f"  SENSITIVE KEY FOUND: {key} = {value}")
    else:
        print(f"Failed to get audit events: {response['status_code']}")

if __name__ == "__main__":
    main()