#!/usr/bin/env python3
"""
Test redaction functionality directly by creating audit events with sensitive data
"""

import asyncio
import sys
import os
sys.path.append('/app/backend')

from app.services.audit import AuditLogger
from app.core.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession

async def test_redaction():
    """Test the redaction functionality directly"""
    
    # Test data with sensitive keys
    sensitive_details = {
        "email": "test@example.com",
        "password": "secret123",
        "token": "bearer-token-123",
        "api_key": "api-key-456",
        "secret": "my-secret",
        "authorization": "Bearer xyz",
        "cookie": "session=abc123",
        "normal_field": "this should not be redacted"
    }
    
    print("Original details:")
    for key, value in sensitive_details.items():
        print(f"  {key}: {value}")
    
    # Test the masking function directly
    from app.services.audit import _mask_sensitive
    
    masked = _mask_sensitive(sensitive_details)
    
    print("\nMasked details:")
    for key, value in masked.items():
        print(f"  {key}: {value}")
    
    # Check if redaction worked
    redacted_keys = []
    non_redacted_sensitive = []
    
    for key, value in masked.items():
        if key.lower() in ["password", "token", "secret", "api_key", "authorization", "cookie"]:
            if value == "[REDACTED]":
                redacted_keys.append(key)
            else:
                non_redacted_sensitive.append(f"{key}={value}")
    
    print(f"\nRedacted keys: {redacted_keys}")
    print(f"Non-redacted sensitive keys: {non_redacted_sensitive}")
    
    if len(redacted_keys) >= 5 and not non_redacted_sensitive:
        print("✅ Redaction working correctly!")
        return True
    else:
        print("❌ Redaction not working properly!")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_redaction())
    sys.exit(0 if success else 1)