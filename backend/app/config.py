import os


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///truss.db")
    HMAC_SECRET: str = os.getenv("HMAC_SECRET", "dev-secret-change-in-prod")
    TRUSS_ESCALATION_TIMEOUT: int = int(os.getenv("TRUSS_ESCALATION_TIMEOUT", "30"))
    TRUSS_ENABLED: bool = os.getenv("TRUSS_ENABLED", "true").lower() == "true"
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")


settings = Settings()
