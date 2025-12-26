from pydantic_settings import BaseSettings
from typing import List, Optional
import json
from arq.connections import RedisSettings

class Settings(BaseSettings):
    # Environment
    env: str = "dev"

    # Database
    database_url: str = "sqlite+aiosqlite:////app/backend/casino.db"
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Auth
    jwt_secret: str = "secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 1440

    # App
    debug: bool = True
    cors_origins: str = '["http://localhost:3000", "http://localhost:3001"]'

    # Logging
    log_level: str = "INFO"
    log_format: str = "auto"

    def get_log_format(self) -> str:
        fmt = (self.log_format or "").strip().lower()
        if fmt in {"plain", "json"}:
            return fmt
        if (self.env or "").lower() in {"prod", "staging"}:
            return "json"
        return "plain"

    trusted_proxy_ips: str = ""
    kill_switch_all: str = "false"
    seed_on_startup: bool = False

    openai_model: str = "gpt-4-1106-preview"
    openai_api_key: Optional[str] = None
    sendgrid_api_key: Optional[str] = None
    sendgrid_from_email: str = "admin@casino.com"
    emergent_llm_key: Optional[str] = None

    kyc_unverified_daily_deposit_cap: float = 100.0
    max_tx_velocity_count: int = 5
    max_tx_velocity_window_minutes: int = 1

    redis_url: str = "redis://redis:6379/0"
    recon_runner: str = "background"

    @property
    def arq_redis_settings(self) -> RedisSettings:
        return RedisSettings.from_dsn(self.redis_url)

    allow_test_payment_methods: bool = True
    ledger_shadow_write: bool = True
    ledger_enforce_balance: bool = False
    ledger_balance_mismatch_log: bool = True

    webhook_signature_enforced: bool = False
    webhook_secret_mockpsp: str = "changeme-mockpsp-secret"
    stripe_api_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    
    adyen_api_key: Optional[str] = None
    adyen_merchant_account: Optional[str] = None
    adyen_client_key: Optional[str] = None
    adyen_hmac_key: Optional[str] = None

    # Audit Retention & Archival (Task D1/D2)
    audit_retention_days: int = 90
    audit_export_secret: str = "change_this_to_strong_secret_for_hmac"
    
    # Task D2: Remote Storage
    audit_archive_backend: str = "filesystem" # 'filesystem' or 's3'
    audit_s3_endpoint: Optional[str] = None
    audit_s3_region: str = "us-east-1"
    audit_s3_bucket: str = "casino-audit-archive"
    audit_s3_access_key: Optional[str] = None
    audit_s3_secret_key: Optional[str] = None
    audit_archive_prefix: str = "audit/"
    # Local path fallback (for 'filesystem' backend)
    audit_archive_path: str = "/app/archive/audit" 

    def get_cors_origins(self) -> List[str]:
        raw = (self.cors_origins or "").strip()
        if not raw:
            if (self.env or "").lower() in {"prod", "staging"}:
                return []
            return ["*"]
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(o).strip() for o in parsed if str(o).strip()]
        except json.JSONDecodeError:
            pass
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        if origins:
            return origins
        if (self.env or "").lower() in {"prod", "staging"}:
            return []
        return ["*"]

    class Config:
        env_file = ".env"
        extra = "ignore"

    def validate_prod_secrets(self) -> None:
        if self.env in {"prod", "staging"}:
            missing = []
            if not self.stripe_api_key or not self.stripe_api_key.startswith("sk_"):
                missing.append("STRIPE_API_KEY (must start with sk_)")
            if not self.stripe_webhook_secret or not self.stripe_webhook_secret.startswith("whsec_"):
                missing.append("STRIPE_WEBHOOK_SECRET (must start with whsec_)")
            
            if not self.adyen_api_key:
                missing.append("ADYEN_API_KEY")
            
            if self.audit_export_secret == "change_this_to_strong_secret_for_hmac":
                missing.append("AUDIT_EXPORT_SECRET (must be changed)")
                
            if self.audit_archive_backend == "s3":
                if not self.audit_s3_access_key: missing.append("AUDIT_S3_ACCESS_KEY")
                if not self.audit_s3_secret_key: missing.append("AUDIT_S3_SECRET_KEY")
                if not self.audit_s3_bucket: missing.append("AUDIT_S3_BUCKET")

            if missing:
                raise ValueError(
                    f"CRITICAL: Missing required secrets for {self.env} environment:\n" + 
                    "\n".join(f"- {m}" for m in missing)
                )

settings = Settings()
