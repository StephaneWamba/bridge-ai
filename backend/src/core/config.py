"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    DEBUG: bool = False
    PROJECT_NAME: str = "BridgeAI"
    VERSION: str = "0.1.0"

    # API
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]  # Allow all origins for development

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5434/bridgeai"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ENCRYPTION_KEY: str = "change-me-in-production-32-chars!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OpenAI
    OPENAI_API_KEY: str = ""

    # HubSpot
    HUBSPOT_CLIENT_ID: str = ""
    HUBSPOT_CLIENT_SECRET: str = ""
    HUBSPOT_REDIRECT_URI: str = "http://localhost:8001/api/v1/integrations/hubspot/callback"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8001/api/v1/integrations/google/callback"

    # Discord
    DISCORD_BOT_TOKEN: str = ""

    # LangGraph
    LANGRAPH_CHECKPOINT_DB_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/bridgeai_checkpoints"


settings = Settings()
