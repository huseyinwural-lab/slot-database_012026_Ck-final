import os
import time
import json
import httpx
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default Constants (Fallback only, prefer ENV)
DEFAULT_BASE_URL = "http://localhost:8001/api/v1"
DEFAULT_ADMIN_EMAIL = "admin@casino.com"
DEFAULT_ADMIN_PASS = "Admin123!"

# Configurable Retry Policies
DEFAULT_RETRY_ATTEMPTS = 5
DEFAULT_RETRY_DELAY = 2.0

def get_env_config():
    """
    Load configuration from environment variables with fallbacks.
    Prioritizes CI-injected variables.
    """
    return {
        "BASE_URL": os.environ.get("API_BASE_URL", DEFAULT_BASE_URL),
        "ADMIN_EMAIL": os.environ.get("BOOTSTRAP_OWNER_EMAIL", os.environ.get("E2E_OWNER_EMAIL", DEFAULT_ADMIN_EMAIL)),
        "ADMIN_PASS": os.environ.get("BOOTSTRAP_OWNER_PASSWORD", os.environ.get("E2E_OWNER_PASSWORD", DEFAULT_ADMIN_PASS)),
        "RETRY_ATTEMPTS": int(os.environ.get("AUTH_RETRY_MAX_ATTEMPTS", DEFAULT_RETRY_ATTEMPTS)),
        "RETRY_DELAY": float(os.environ.get("AUTH_RETRY_BASE_DELAY_SEC", DEFAULT_RETRY_DELAY))
    }

def sanitize_log(data):
    """
    Recursively mask sensitive fields in logs to prevent credential leakage.
    Handles strings (if JSON), dicts, and lists.
    """
    if isinstance(data, str):
        try:
            # Try parsing as JSON to mask fields inside
            parsed = json.loads(data)
            return json.dumps(sanitize_log(parsed))
        except:
            # If plain string, check for basic patterns (simple heuristic)
            if "Bearer " in data:
                return data.split("Bearer ")[0] + "Bearer ***REDACTED***"
            return data
            
    if isinstance(data, dict):
        masked = data.copy()
        sensitive_keys = {
            "access_token", "refresh_token", "password", "token", 
            "authorization", "api_key", "secret", "client_secret"
        }
        for key in masked:
            if key.lower() in sensitive_keys:
                masked[key] = "***REDACTED***"
            else:
                masked[key] = sanitize_log(masked[key])
        return masked
        
    if isinstance(data, list):
        return [sanitize_log(item) for item in data]
        
    return data

async def login_admin_with_retry(client: httpx.AsyncClient):
    config = get_env_config()
    url = f"{config['BASE_URL']}/auth/login"
    payload = {"email": config["ADMIN_EMAIL"], "password": config["ADMIN_PASS"]}
    
    retries = config["RETRY_ATTEMPTS"]
    delay = config["RETRY_DELAY"]
    
    logger.info(f"Attempting login to {config['BASE_URL']} as {config['ADMIN_EMAIL']}... (Max Retries: {retries})")
    
    for attempt in range(1, retries + 1):
        try:
            resp = await client.post(url, json=payload)
            
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("access_token")
                if token:
                    logger.info("Login successful.")
                    return token
                else:
                    # Security: Log sanitized body
                    logger.error(f"Login 200 OK but missing token. Response: {sanitize_log(data)}")
                    # Fail fast on protocol error (200 but no token is unexpected)
                    raise ValueError("Login response missing access_token")
            elif resp.status_code in {401, 403}:
                # Auth failure - check credentials or seeding
                logger.warning(f"Auth failed (Attempt {attempt}/{retries}). Status: {resp.status_code}. Response: {sanitize_log(resp.text)}")
            else:
                # Server error / Timeout - worthy of retry
                logger.warning(f"Server error (Attempt {attempt}/{retries}). Status: {resp.status_code}")
                
        except httpx.RequestError as e:
            logger.warning(f"Network error during login (Attempt {attempt}/{retries}): {e}")
            
        if attempt < retries:
            sleep_time = delay * (attempt) # Linear backoff
            logger.info(f"Retrying in {sleep_time}s...")
            time.sleep(sleep_time)
            
    raise RuntimeError(f"Max login retries ({retries}) exceeded. Could not authenticate.")

def get_auth_headers(token):
    return {
        "Authorization": f"Bearer {token}", 
        "Content-Type": "application/json",
        "X-Request-ID": str(uuid.uuid4()) # Traceability
    }
