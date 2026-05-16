"""
Centralized application configuration.
All secrets and settings are loaded from environment variables
with validation via pydantic-settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── App ─────────────────────────────────────────────
    APP_NAME: str = "ViralClips AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = Field(default="production", description="dev | staging | production")

    # ── Server ──────────────────────────────────────────
    PORT: int = 8080
    HOST: str = "0.0.0.0"
    ALLOWED_ORIGINS: str = Field(
        default="https://viral-clips-ai-9911-7f495.web.app,http://localhost:3000",
        description="Comma-separated list of allowed CORS origins",
    )

    # ── Gemini AI ───────────────────────────────────────
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_MAX_RETRIES: int = 3
    GEMINI_TIMEOUT: int = 60

    # ── Database ────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./viralclips.db",
        description="Async database connection string",
    )

    # ── Redis / Celery ──────────────────────────────────
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    CELERY_BROKER_URL: Optional[str] = None  # Falls back to REDIS_URL
    CELERY_RESULT_BACKEND: Optional[str] = None

    # ── Firebase ────────────────────────────────────────
    FIREBASE_PROJECT_ID: str = "viral-clips-ai-9911"
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None  # Path to service account JSON

    # ── Storage ─────────────────────────────────────────
    GCS_BUCKET: str = Field(default="viral-clips-ai-9911-clips", description="GCS bucket for processed clips")
    TEMP_DIR: str = Field(default="/tmp/viralclips", description="Temporary file storage")
    MAX_UPLOAD_SIZE_MB: int = 2048  # 2GB

    # ── Video Processing ────────────────────────────────
    FFMPEG_THREADS: int = 2
    WHISPER_MODEL: str = "base"  # tiny | base | small | medium | large-v3
    MAX_VIDEO_DURATION_MINUTES: int = 120

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def celery_broker(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def celery_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton for application settings."""
    return Settings()
