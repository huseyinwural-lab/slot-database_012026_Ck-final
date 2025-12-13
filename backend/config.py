from pydantic_settings import BaseSettings
from typing import List, Optional
import json

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./casino.db" # Default to SQLite for ease of run
    
    # Auth
    jwt_secret: str = "secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 1440
    
    # App
    debug: bool = True
    cors_origins: str = '["http://localhost:3000", "http://localhost:3001"]'
    
    openai_model: str = "gpt-4-1106-preview"
    # Integrations
    openai_api_key: Optional[str] = None
    
    # Legacy/Other (Just in case other files ref it)
    mongo_url: Optional[str] = None
    db_name: str = "casino_db"

    def get_cors_origins(self) -> List[str]:
        try:
            return json.loads(self.cors_origins)
        except json.JSONDecodeError:
            return ["*"]

    class Config:
        env_file = ".env"
        extra = "ignore" # Ignore extra fields in .env

settings = Settings()
