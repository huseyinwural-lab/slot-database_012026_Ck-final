from pydantic_settings import BaseSettings
from typing import List
import json

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/casino_db"
    jwt_secret: str = "secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 1440
    debug: bool = True
    cors_origins: str = '["http://localhost:3000", "http://localhost:3001"]'

    def get_cors_origins(self) -> List[str]:
        try:
            return json.loads(self.cors_origins)
        except json.JSONDecodeError:
            return ["*"]

    class Config:
        env_file = ".env"

settings = Settings()
