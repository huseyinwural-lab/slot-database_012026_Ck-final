import os
import time
import json
import httpx
import logging

# Configure minimal logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default Constants (Fallback only, prefer ENV)
DEFAULT_BASE_URL = "http://localhost:8001/api/v1"
DEFAULT_ADMIN_EMAIL = "admin@casino.com"
DEFAULT_ADMIN_PASS = "Admin123!"

def get_env_config():
    return {
        "BASE_URL": os.environ.get("API_BASE_URL", DEFAULT_BASE_URL),
        "ADMIN_EMAIL": os.environ.get("BOOTSTRAP_OWNER_EMAIL", DEFAULT_ADMIN_EMAIL),
        "ADMIN_PASS": os.environ.get("BOOTSTRAP_OWNER_PASSWORD", DEFAULT_ADMIN_PASS)
    }

async def login_admin_with_retry(client: httpx.AsyncClient, retries=5, backoff_factor=2):
    config = get_env_config()
    url = f"{config['BASE_URL']}/auth/login"
    payload = {"email": config["ADMIN_EMAIL"], "password": config["ADMIN_PASS"]}
    
    logger.info(f"Attempting login to {config['BASE_URL']} as {config['ADMIN_EMAIL']}...")
    
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
                    logger.error(f"Login response 200 OK but missing access_token. Body: {sanitize_log(data)}")
                    # If 200 but no token, retry might not help unless it's a weird race, but let's fail fast usually.
                    # Actually, let's treat as fail.
            else:
                logger.warning(f"Login failed (Attempt {attempt}/{retries}). Status: {resp.status_code}. Body: {sanitize_log(resp.text)}")
                
        except httpx.RequestError as e:
            logger.warning(f"Network error during login (Attempt {attempt}/{retries}): {e}")
            
        if attempt < retries:
            sleep_time = backoff_factor ** (attempt - 1)
            logger.info(f"Retrying in {sleep_time}s...")
            time.sleep(sleep_time)
            
    raise RuntimeError("Max login retries exceeded. Could not authenticate.")

def sanitize_log(data):
    """Mask sensitive fields in logs."""
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            return data # Return raw string if not JSON
            
    if isinstance(data, dict):
        masked = data.copy()
        for key in ["access_token", "refresh_token", "password", "token"]:
            if key in masked:
                masked[key] = "***REDACTED***"
        return json.dumps(masked)
    return str(data)

def get_auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
