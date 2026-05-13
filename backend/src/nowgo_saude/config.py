"""Application configuration loaded via pydantic-settings.

The MVP defaults to SQLite for the local dev/test loop. Production deployments
should override DATABASE_URL with a PostgreSQL DSN (per the data-model spec).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NOWGO_",
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    environment: str = Field(default="dev")
    database_url: str = Field(default="sqlite+pysqlite:///./nowgo_saude.db")
    admin_token: str = Field(default="test-admin-token")
    lgpd_officer_token: str = Field(default="test-lgpd-officer-token")
    pii_token_secret: str = Field(default="dev-pii-secret-change-me")
    pii_vault_key: str = Field(
        default="ZGV2LXBpaS12YXVsdC1rZXktY2hhbmdlLW1lLTAwMDA=",
        description="Base64-encoded 32-byte AES-256-GCM key (current generation).",
    )
    pii_vault_key_version: int = Field(default=1, ge=1)
    classifier_low_confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    health_latency_threshold_seconds: float = Field(
        default=300.0,
        ge=1.0,
        description=(
            "Maximum age (seconds) of the most recent classified event before"
            " /api/v1/dashboard/health flips to 'degraded'. Raise this while"
            " demoing static seed data ahead of live adapters (Phase H)."
        ),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
