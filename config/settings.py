"""Pydantic settings for Polaris."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for Polaris evaluation system.

    Loads from environment variables or .env file.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql://polaris:polaris@localhost:5432/polaris"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_keys: list[str] = ["dev-key-12345"]  # In production: load from secrets

    # Rate limiting
    rate_limit_per_minute: int = 10

    # Worker
    rq_queue_name: str = "polaris"
    rq_redis_url: str | None = None  # Falls back to redis_url if not set

    @property
    def worker_redis_url(self) -> str:
        """Get Redis URL for worker, with fallback to main redis_url."""
        return self.rq_redis_url or self.redis_url
