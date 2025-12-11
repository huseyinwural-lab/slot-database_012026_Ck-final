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
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")

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
