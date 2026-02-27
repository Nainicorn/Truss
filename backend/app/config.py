import os
import warnings


_DEFAULT_HMAC_SECRET = "dev-secret-change-in-prod"


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///truss.db")
    HMAC_SECRET: str = os.getenv("HMAC_SECRET", _DEFAULT_HMAC_SECRET)
    TRUSS_ESCALATION_TIMEOUT: int = int(os.getenv("TRUSS_ESCALATION_TIMEOUT", "30"))
    TRUSS_ENABLED: bool = os.getenv("TRUSS_ENABLED", "true").lower() == "true"
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    @property
    def hmac_secret_is_default(self) -> bool:
        return self.HMAC_SECRET == _DEFAULT_HMAC_SECRET


settings = Settings()

if settings.hmac_secret_is_default:
    warnings.warn(
        "HMAC_SECRET is using the default dev value. "
        "Set HMAC_SECRET environment variable for production deployments. "
        "Audit signatures are not secure with the default key.",
        stacklevel=1,
    )
