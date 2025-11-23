"""Centralized configuration for ThreatVeilAI backend."""
import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings
    SettingsConfigDict = None

from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Frontend
    next_public_app_name: str = Field(default="ThreatVeilAI")
    next_public_api_base: str = Field(default="http://127.0.0.1:8000")

    # Backend
    allowed_origins: str = Field(default="http://localhost:3000")
    user_agent: str = Field(default="ThreatVeilScanner/0.1 (+https://threatveil.com)")

    # Database
    database_url: Optional[str] = Field(default=None)
    sqlite_path: str = Field(default="./backend/app.db")
    supabase_service_role_key: Optional[str] = Field(default=None)

    # API Keys (all optional except GEMINI_API_KEY for full functionality)
    gemini_api_key: Optional[str] = Field(default=None)
    github_token: Optional[str] = Field(default=None)
    vulners_api_key: Optional[str] = Field(default=None)
    otx_api_key: Optional[str] = Field(default=None)
    lakera_api_key: Optional[str] = Field(default=None)
    resend_api_key: Optional[str] = Field(default=None)

    # Security
    jwt_secret: str = Field(default="change_me")
    rate_limit_per_minute: int = Field(default=60)

    # Optional Integrations
    slack_webhook_url: Optional[str] = Field(default=None)

    # Server
    port: int = Field(default=8000)
    environment: str = Field(default="development")
    log_level: str = Field(default="info")

    if SettingsConfigDict:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
        )
    else:
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False


# Global settings instance
settings = Settings()

