"""Application configuration and settings management."""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # API Configuration
    API_TITLE: str = "AI Incident Analyzer API"
    API_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"

    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ai_incident_analyzer"
    SQLALCHEMY_ECHO: bool = False

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Configuration
    SECRET_KEY: str = "dev-secret-key-not-for-production-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Google Gemini API
    GEMINI_API_KEY: str = "your-gemini-api-key-here"

    # Qdrant Vector Database
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION_NAME: str = "incidents"

    # File Upload Configuration
    MAX_UPLOAD_SIZE_MB: int = 5
    MAX_ANALYSIS_LOG_CHARS: int = 30000
    UPLOAD_DIRECTORY: str = "uploads/logs"

    # CORS Configuration
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173", "http://localhost:3000"]

    @model_validator(mode="after")
    def validate_production_secret(self) -> "Settings":
        """Reject known development secrets when configured for production."""
        unsafe_secrets = {
            "dev-secret-key-not-for-production-change-me",
            "replace-with-a-long-random-secret",
            "local-only-change-me",
            "dev-secret-key-change-in-production",
        }
        if self.ENVIRONMENT.lower() == "production" and (
            self.SECRET_KEY in unsafe_secrets or len(self.SECRET_KEY) < 32
        ):
            raise ValueError(
                "SECRET_KEY must be a unique random value of at least 32 characters in production")
        return self

    @property
    def max_upload_size_bytes(self) -> int:
        """Convert max upload size from MB to bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"


# Global settings instance
settings = Settings()  # type: ignore
