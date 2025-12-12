import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    sendgrid_api_key: str = os.getenv("SENDGRID_API_KEY", "")
    
    # Database
    mongo_url: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name: str = os.getenv("DB_NAME", "casino_admin_db")
    
    # Application
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    def get_cors_origins(self) -> list[str]:
        # If explicit allowed origins are provided, use them
        raw = (self.cors_allowed_origins or "").strip()
        if raw in ("", "*"):
            # Fallbacks by environment
            if self.environment in ("development", "local", "dev"):
                return [
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                ]
            # For prod/stage, do NOT fall back to '*'; require explicit list
            return []
        # Support comma-separated list
        return [o.strip() for o in raw.split(",") if o.strip()]
    cors_allowed_origins: str = os.getenv("CORS_ALLOWED_ORIGINS", "*")

    # Auth / JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-dev-secret")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expires_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60"))
    
    # SendGrid
    sendgrid_from_email: str = os.getenv("SENDGRID_FROM_EMAIL", "noreply@casinoadmin.com")
    
    # OpenAI
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    emergent_llm_key: Optional[str] = None
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
