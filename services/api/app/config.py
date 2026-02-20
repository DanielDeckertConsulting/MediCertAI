"""Application configuration. Secrets from env or Key Vault."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    database_url: str = "postgresql+asyncpg://clinai:clinai@localhost:5432/clinai"
    auth_bypass_local: bool = True  # Skip JWT validation when True (local dev only)
    rate_limit_per_minute: int = 100
    cors_origins: str = "http://localhost:5173"

    # Azure OpenAI (Phase 1.1)
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str | None = None
    azure_openai_api_version: str = "2024-02-15-preview"

    # Message limits (prompt injection mitigation)
    max_user_message_length: int = 8000

    # AI Response confidence threshold (below = route to review)
    ai_confidence_threshold: float = 0.85

    # B2C (production)
    b2c_tenant: str | None = None
    b2c_client_id: str | None = None
    b2c_audience: str | None = None
    b2c_openid_config_url: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def azure_openai_configured(self) -> bool:
        return bool(
            self.azure_openai_endpoint
            and self.azure_openai_api_key
            and self.azure_openai_deployment
        )


settings = Settings()
