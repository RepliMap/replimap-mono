"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://localhost/replimap"

    # Security
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Admin API key (required for admin endpoints)
    admin_api_key: str | None = None

    # License signing (for generating license keys)
    license_signing_key: str = "change-me-in-production"

    # Stripe (optional, for payment integration)
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_id_starter: str | None = None
    stripe_price_id_team: str | None = None
    stripe_price_id_enterprise: str | None = None

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Feature flags
    enable_usage_tracking: bool = True
    enable_activation_limits: bool = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
