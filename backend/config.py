from pydantic_settings import BaseSettings
from typing import List, Optional
import json

class Settings(BaseSettings):
    # Environment
    # Canonical values: dev | local | staging | prod
    env: str = "dev"  # ENV

    # Database
    database_url: str = "sqlite+aiosqlite:///./casino.db"  # Default to SQLite for ease of run
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

    # Kill switch
    # Global emergency switch to disable all non-core modules
    kill_switch_all: str = "false"  # KILL_SWITCH_ALL

    openai_model: str = "gpt-4-1106-preview"
    # Integrations
    openai_api_key: Optional[str] = None
    
    sendgrid_api_key: Optional[str] = None
    sendgrid_from_email: str = "admin@casino.com"
    emergent_llm_key: Optional[str] = None
    # DEPRECATED (MongoDB was removed; kept temporarily to avoid breaking legacy scripts)
    # Planned removal: Patch 3 repo cleanup.
    mongo_url: Optional[str] = None
    db_name: str = "casino_db"

    def get_cors_origins(self) -> List[str]:
        raw = (self.cors_origins or "").strip()
        if not raw:
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
        return origins or ["*"]

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env

settings = Settings()
