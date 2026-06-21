"""
Application configuration via environment variables.

Uses pydantic-settings so all values can be overridden with env vars
or a .env file during local development.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Feature flags (USE_*) default to True for production-like behaviour.
    Set them to False in local development to avoid needing external credentials.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -----------------------------------------------------------------------
    # OpenRouter AI
    # -----------------------------------------------------------------------
    OPENROUTER_API_KEY: str = Field(
        default="",
        description="OpenRouter API key (required when USE_OPENROUTER=true)",
    )
    OPENROUTER_BASE_URL: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL",
    )
    OPENROUTER_MODEL: str = Field(
        default="google/gemini-2.5-flash",
        description="OpenRouter model identifier (e.g. google/gemini-2.5-flash)",
    )

    # -----------------------------------------------------------------------
    # Supabase / PostgreSQL
    # -----------------------------------------------------------------------
    SUPABASE_DB_URL: str = Field(
        default="",
        description=(
            "PostgreSQL connection string for Supabase or any PostgreSQL host. "
            "Format: postgresql://user:password@host:port/dbname"
        ),
    )

    @field_validator("SUPABASE_DB_URL", mode="before")
    @classmethod
    def sanitize_database_url(cls, v: Any) -> Any:
        if isinstance(v, str) and v:
            import urllib.parse
            try:
                # Expected format: postgresql://username:password@host:port/database
                if "://" not in v:
                    return v
                scheme, rest = v.split("://", 1)
                # Split database part
                if "/" in rest:
                    host_part, db_part = rest.rsplit("/", 1)
                else:
                    host_part, db_part = rest, ""
                
                # Split host/port from user/pass (last @ symbol)
                if "@" in host_part:
                    user_pass, host_port = host_part.rsplit("@", 1)
                else:
                    return v  # No userinfo part
                
                # Split user and password (first : symbol in userinfo)
                if ":" in user_pass:
                    user, password = user_pass.split(":", 1)
                    # URL-encode the password safely (unquote first to avoid double encoding)
                    encoded_password = urllib.parse.quote(urllib.parse.unquote(password))
                    sanitized_user_pass = f"{user}:{encoded_password}"
                else:
                    sanitized_user_pass = user_pass
                    
                sanitized_url = f"{scheme}://{sanitized_user_pass}@{host_port}"
                if db_part:
                    sanitized_url = f"{sanitized_url}/{db_part}"
                return sanitized_url
            except Exception:
                # Fallback to original if anything fails
                return v
        return v

    # -----------------------------------------------------------------------
    # Feature Flags
    # -----------------------------------------------------------------------
    USE_OPENROUTER: bool = Field(
        default=True,
        description="Enable OpenRouter AI for insights (requires OPENROUTER_API_KEY)",
    )
    # Backward-compatible alias: USE_GEMINI maps to USE_OPENROUTER
    USE_GEMINI: bool = Field(
        default=True,
        description="Alias for USE_OPENROUTER â€” kept for CI compatibility",
    )
    USE_SUPABASE: bool = Field(
        default=True,
        description="Enable Supabase PostgreSQL persistence (requires SUPABASE_DB_URL)",
    )
    # Backward-compatible alias: USE_FIRESTORE maps to USE_SUPABASE
    USE_FIRESTORE: bool = Field(
        default=True,
        description="Alias for USE_SUPABASE â€” kept for CI compatibility",
    )
    USE_ANALYTICS: bool = Field(
        default=True,
        description="Enable PostgreSQL analytics logging",
    )
    # Backward-compatible alias: USE_BIGQUERY maps to USE_ANALYTICS
    USE_BIGQUERY: bool = Field(
        default=True,
        description="Alias for USE_ANALYTICS â€” kept for CI compatibility",
    )
    USE_EVENT_QUEUE: bool = Field(
        default=True,
        description="Enable database-backed event queue",
    )
    # Backward-compatible alias: USE_PUBSUB maps to USE_EVENT_QUEUE
    USE_PUBSUB: bool = Field(
        default=True,
        description="Alias for USE_EVENT_QUEUE â€” kept for CI compatibility",
    )

    # -----------------------------------------------------------------------
    # Application
    # -----------------------------------------------------------------------
    ENVIRONMENT: str = Field(
        default="development",
        description="Runtime environment: development | staging | production",
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Python logging level: DEBUG | INFO | WARNING | ERROR",
    )
    MAX_HISTORY_ENTRIES: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of history entries returned per device",
    )

    # -----------------------------------------------------------------------
    # Resolved feature flags (consolidate aliases)
    # -----------------------------------------------------------------------

    @property
    def ai_enabled(self) -> bool:
        """True if AI insights are enabled (checks both old and new flag names)."""
        return self.USE_OPENROUTER and self.USE_GEMINI

    @property
    def db_enabled(self) -> bool:
        """True if database persistence is enabled."""
        return self.USE_SUPABASE and self.USE_FIRESTORE

    @property
    def analytics_enabled(self) -> bool:
        """True if analytics logging is enabled."""
        return self.USE_ANALYTICS and self.USE_BIGQUERY

    @property
    def event_queue_enabled(self) -> bool:
        """True if the event queue is enabled."""
        return self.USE_EVENT_QUEUE and self.USE_PUBSUB


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings (singleton)."""
    return Settings()


def validate_config(settings: Settings | None = None) -> None:
    """
    Validate required environment variables at application startup.

    Logs a warning (not an error) for missing optional credentials so the
    app still starts in development mode without external services configured.

    Args:
        settings: Optional Settings instance; uses cached singleton if None.
    """
    s = settings or get_settings()
    issues: list[str] = []

    if s.ai_enabled and not s.OPENROUTER_API_KEY:
        issues.append(
            "OPENROUTER_API_KEY is not set but USE_OPENROUTER=true. "
            "AI insights will fall back to the rule engine."
        )

    if s.db_enabled and not s.SUPABASE_DB_URL:
        issues.append(
            "SUPABASE_DB_URL is not set but USE_SUPABASE=true. "
            "Entries will be stored in memory (lost on restart)."
        )

    for issue in issues:
        logger.warning("Config warning: %s", issue)

    if issues:
        logger.info(
            "EcoTracker: %d config warning(s). "
            "Set USE_OPENROUTER=false and USE_SUPABASE=false for local dev without credentials.",
            len(issues),
        )
    else:
        logger.info("EcoTracker: configuration validated successfully.")
