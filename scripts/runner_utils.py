import os
import time
import json
import httpx
import logging
import uuid
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default Constants (Fallback only)
DEFAULT_BASE_URL = "http://localhost:8001/api/v1"
DEFAULT_ADMIN_EMAIL = "admin@casino.com"
DEFAULT_ADMIN_PASS = "Admin123!"

# Configurable Retry Policies
DEFAULT_RETRY_ATTEMPTS = 5
DEFAULT_RETRY_DELAY = 2.0
MAX_LOG_LENGTH = 4096  # Truncate logs > 4KB

def get_env_config():
    """
    Load configuration from environment variables with fallbacks.
    If CI_STRICT=1 is set, fail fast on missing required variables.
    """
    strict_mode = os.environ.get("CI_STRICT", "0") == "1"
    
    config = {
        "BASE_URL": os.environ.get("API_BASE_URL"),
        "ADMIN_EMAIL": os.environ.get("BOOTSTRAP_OWNER_EMAIL", os.environ.get("E2E_OWNER_EMAIL")),
        "ADMIN_PASS": os.environ.get("BOOTSTRAP_OWNER_PASSWORD", os.environ.get("E2E_OWNER_PASSWORD")),
        "RETRY_ATTEMPTS": int(os.environ.get("AUTH_RETRY_MAX_ATTEMPTS", DEFAULT_RETRY_ATTEMPTS)),
        "RETRY_DELAY": float(os.environ.get("AUTH_RETRY_BASE_DELAY_SEC", DEFAULT_RETRY_DELAY))
    }

    # Strict Mode Validation
    if strict_mode:
        missing = []
        if not config["BASE_URL"]: missing.append("API_BASE_URL")
        if not config["ADMIN_EMAIL"]: missing.append("BOOTSTRAP_OWNER_EMAIL")
        if not config["ADMIN_PASS"]: missing.append("BOOTSTRAP_OWNER_PASSWORD")
        
        if missing:
            logger.critical(f"[CI_STRICT] Missing required env vars: {', '.join(missing)}")
            sys.exit(2) # Config Error

    # Fallbacks for non-strict mode
    if not config["BASE_URL"]: config["BASE_URL"] = DEFAULT_BASE_URL
    if not config["ADMIN_EMAIL"]: config["ADMIN_EMAIL"] = DEFAULT_ADMIN_EMAIL
    if not config["ADMIN_PASS"]: config["ADMIN_PASS"] = DEFAULT_ADMIN_PASS
    
    # Policy Bounds
    config["RETRY_ATTEMPTS"] = min(max(1, config["RETRY_ATTEMPTS"]), 10) # 1-10
    config["RETRY_DELAY"] = min(max(0.1, config["RETRY_DELAY"]), 5.0) # 0.1s - 5s

    return config

def sanitize_log(data):
    """
    Recursively mask sensitive fields in logs to prevent credential leakage.
    Handles strings (if JSON), dicts, and lists. Truncates long outputs.
    """
    if data is None:
        return None

    # Handle Length
    str_data = str(data)
    if len(str_data) > MAX_LOG_LENGTH:
        return str_data[:MAX_LOG_LENGTH] + "... [TRUNCATED]"

    # Recursive Masking
    if isinstance(data, str):
        try:
            # Try parsing as JSON to mask fields inside
            parsed = json.loads(data)
            return json.dumps(sanitize_log(parsed))
        except:
            # Basic string replacement
            sensitive_patterns = ["Bearer ", "access_token=", "password="]
            for pat in sensitive_patterns:
                if pat in data:
                    parts = data.split(pat)
                    return parts[0] + pat + "***REDACTED***" + (parts[1][20:] if len(parts[1]) > 20 else "")
            return data
            
    if isinstance(data, dict):
        masked = data.copy()
        sensitive_keys = {
            "access_token", "refresh_token", "id_token", "password", "token", 
            "authorization", "api_key", "secret", "client_secret", "cookie", "set-cookie"
        }
        for key in masked:
            if str(key).lower() in sensitive_keys:
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
                    logger.error(f"Login 200 OK but missing token. Response: {sanitize_log(data)}")
                    # Protocol error, fail fast unless it's a known race condition
                    raise ValueError("Login response missing access_token")
            elif resp.status_code in {401, 403}:
                # Auth failure - limited retry for seed propagation (max 2)
                if attempt > 2:
                    logger.error(f"Auth failed permanently after 2 attempts. Status: {resp.status_code}")
                    raise ValueError(f"Authentication failed: {resp.status_code}")
                logger.warning(f"Auth failed (Attempt {attempt}/{retries}). Seed might be pending...")
            elif resp.status_code >= 500:
                logger.warning(f"Server error (Attempt {attempt}/{retries}). Status: {resp.status_code}")
            else:
                logger.warning(f"Unexpected status (Attempt {attempt}/{retries}). Status: {resp.status_code}")
                
        except (httpx.RequestError, httpx.TimeoutException) as e:
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
        "X-Request-ID": str(uuid.uuid4())
    }
