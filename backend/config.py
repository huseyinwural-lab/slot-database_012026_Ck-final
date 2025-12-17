from pydantic_settings import BaseSettings
from typing import List, Optional
import json

class Settings(BaseSettings):
    # Environment
    # Canonical values: dev | local | staging | prod
    env: str = "dev"  # ENV

    # Database
    database_url: str = "sqlite+aiosqlite:////app/backend/casino.db"  # Absolute path to prevent CWD mismatch
    # Connection pool tuning (Postgres/asyncpg)
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Auth
    jwt_secret: str = "secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 1440

    # App
    debug: bool = True
    # Supports both formats:
    # 1) JSON list: ["http://localhost:3000", "http://localhost:3001"]
    # 2) CSV: http://localhost:3000,http://localhost:3001
    cors_origins: str = '["http://localhost:3000", "http://localhost:3001"]'

    # Logging
    log_level: str = "INFO"  # LOG_LEVEL
    # Default: auto => dev/local plain, prod/staging json
    log_format: str = "auto"  # LOG_FORMAT (auto|plain|json)

    def get_log_format(self) -> str:
        fmt = (self.log_format or "").strip().lower()
        if fmt in {"plain", "json"}:
            return fmt
        # auto/empty/unknown -> env-based default
        if (self.env or "").lower() in {"prod", "staging"}:
            return "json"
        return "plain"

    # Reverse proxy / client IP trust
    # Comma-separated list of trusted proxy IPs (the immediate peer IP that forwards requests).
    # Only when ENV is prod/staging and the request comes from a trusted proxy IP
    # will we trust X-Forwarded-For for rate limiting.
    trusted_proxy_ips: str = ""  # TRUSTED_PROXY_IPS

    # Kill switch
    # Global emergency switch to disable all non-core modules
    kill_switch_all: str = "false"  # KILL_SWITCH_ALL

    # Seeding guard (P0)
    # Fail-closed: seed runs only in (dev|local) AND when explicitly enabled.
    seed_on_startup: bool = False  # SEED_ON_STARTUP

    openai_model: str = "gpt-4-1106-preview"
    # Integrations
    openai_api_key: Optional[str] = None
    
    sendgrid_api_key: Optional[str] = None
    sendgrid_from_email: str = "admin@casino.com"
    emergent_llm_key: Optional[str] = None

    def get_cors_origins(self) -> List[str]:
        raw = (self.cors_origins or "").strip()
        if not raw:
            # In prod/staging we fail-closed (no wildcard). In dev/local we keep permissive behavior.
            if (self.env or "").lower() in {"prod", "staging"}:
                return []
            return ["*"]

        # JSON list support (legacy)
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(o).strip() for o in parsed if str(o).strip()]
        except json.JSONDecodeError:
            pass

        # CSV support (canonical for prod)
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        if origins:
            return origins

        if (self.env or "").lower() in {"prod", "staging"}:
            return []
        return ["*"]

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env

settings = Settings()
