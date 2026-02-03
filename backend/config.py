from pydantic_settings import BaseSettings
from pydantic import AliasChoices, Field, model_validator
from typing import List, Optional
import json
from arq.connections import RedisSettings

class Settings(BaseSettings):
    # Environment
    env: str = "dev"

    # Database
    database_url: str = "sqlite+aiosqlite:////app/backend/casino.db"
    # Optional explicit sync URL for Alembic / sync tooling.
    # Supports both env names for backward compatibility.
    sync_database_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("SYNC_DATABASE_URL", "DATABASE_URL_SYNC"),
    )
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

    # Email (Resend)
    resend_api_key: Optional[str] = Field(default=None, validation_alias=AliasChoices("RESEND_API_KEY"))
    resend_from: str = Field(default="onboarding@resend.dev", validation_alias=AliasChoices("RESEND_FROM"))
    resend_reply_to: Optional[str] = Field(default=None, validation_alias=AliasChoices("RESEND_REPLY_TO"))
    resend_test_to: Optional[str] = Field(default=None, validation_alias=AliasChoices("RESEND_TEST_TO"))

    emergent_llm_key: Optional[str] = None

    kyc_unverified_daily_deposit_cap: float = 100.0
    max_tx_velocity_count: int = 5
    max_tx_velocity_window_minutes: int = 1
    register_velocity_limit: int = Field(default=100, validation_alias=AliasChoices("REGISTER_VELOCITY_LIMIT"))


    # Player frontend base URL (used for payment redirect construction when Origin header is absent)
    player_app_url: str = "http://localhost:3001"

    # Redis / Queue

    stripe_mock: bool = False

    # Default is localhost to avoid docker-compose host coupling.
    # In prod/staging, Redis is OPTIONAL unless REDIS_REQUIRED=true.
    redis_url: str = "redis://localhost:6379/0"
    redis_required: bool = False

    # If REDIS_URL is unset/blank, keep a safe default unless Redis is required.
    # (Pydantic will otherwise override the default with an empty string.)
    @model_validator(mode="after")
    def _normalize_redis_url(self):
        if (self.redis_url or "").strip() == "":
            self.redis_url = "redis://localhost:6379/0"
        return self
    recon_runner: str = "background"

    @property
    def arq_redis_settings(self) -> RedisSettings:
        return RedisSettings.from_dsn(self.redis_url)

    allow_test_payment_methods: bool = True
    ledger_shadow_write: bool = True
    ledger_enforce_balance: bool = False
    ledger_balance_mismatch_log: bool = True

    webhook_signature_enforced: bool = False

    # Generic webhook signature (used by finance payout webhook endpoint)
    webhook_secret: Optional[str] = Field(default=None, validation_alias=AliasChoices("WEBHOOK_SECRET"))
    webhook_test_secret: Optional[str] = Field(default=None, validation_alias=AliasChoices("WEBHOOK_TEST_SECRET"))

    webhook_secret_mockpsp: str = "changeme-mockpsp-secret"
    stripe_api_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    
    adyen_api_key: Optional[str] = None
    adyen_merchant_account: Optional[str] = None
    adyen_client_key: Optional[str] = None
    adyen_hmac_key: Optional[str] = None

    # KYC (mock UI endpoints)
    kyc_mock_enabled: bool = True

    # Audit Retention
    audit_retention_days: int = 90
    audit_export_secret: str = "change_this_to_strong_secret_for_hmac"
    
    # Storage
    audit_archive_backend: str = "filesystem"
    audit_s3_endpoint: Optional[str] = None
    audit_s3_region: str = "us-east-1"
    audit_s3_bucket: str = "casino-audit-archive"
    audit_s3_access_key: Optional[str] = None
    audit_s3_secret_key: Optional[str] = None
    audit_archive_prefix: str = "audit/"
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
        """P0-OPS-001: Strict Production Validation."""
        if self.env in {"prod", "staging"}:
            missing = []
            # Critical Secrets List - MUST BE LIVE keys
            # Only enforce live-key checks in PROD.
            if self.env == "prod":
                if not self.stripe_api_key or "live" not in self.stripe_api_key:
                    missing.append("STRIPE_API_KEY (must contain 'live')")
                if not self.stripe_webhook_secret:
                    missing.append("STRIPE_WEBHOOK_SECRET")

                if not self.adyen_api_key:
                    missing.append("ADYEN_API_KEY")
            else:
                # Staging: require presence but allow non-live keys.
                if not self.stripe_api_key:
                    missing.append("STRIPE_API_KEY")
                if not self.stripe_webhook_secret:
                    missing.append("STRIPE_WEBHOOK_SECRET")
                if not self.adyen_api_key:
                    missing.append("ADYEN_API_KEY")

            # Webhook security (P0)
            if not self.adyen_hmac_key:
                missing.append("ADYEN_HMAC_KEY")

            # KYC mock endpoints must be disabled in prod/staging
            if self.kyc_mock_enabled:
                missing.append("KYC_MOCK_ENABLED (must be false in prod/staging)")
            
            if self.audit_export_secret == "change_this_to_strong_secret_for_hmac":
                missing.append("AUDIT_EXPORT_SECRET (must be changed)")
                
            if self.audit_archive_backend == "s3":
                if not self.audit_s3_access_key:
                    missing.append("AUDIT_S3_ACCESS_KEY")
                if not self.audit_s3_secret_key:
                    missing.append("AUDIT_S3_SECRET_KEY")
                if not self.audit_s3_bucket:
                    missing.append("AUDIT_S3_BUCKET")

            if missing:
                raise ValueError(
                    f"CRITICAL: Missing required secrets for {self.env} environment:\n" + 
                    "\n".join(f"- {m}" for m in missing)
                )

settings = Settings()
