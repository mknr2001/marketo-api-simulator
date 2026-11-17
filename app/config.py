"""Application configuration using pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "Marketo API Simulator"
    APP_ENV: str = "local"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./marketo_simulator.db"

    # ── Authentication ───────────────────────────────────────────
    MOCK_CLIENT_ID: str = "marketo-poc-client"
    MOCK_CLIENT_SECRET: str = "change-me"
    ACCESS_TOKEN_TTL_SECONDS: int = 3599
    TOKEN_HASH_SECRET: str = "replace-with-a-long-random-value"

    # ── Export Processing ────────────────────────────────────────
    QUEUE_DELAY_SECONDS: int = 2
    PROCESSING_DELAY_SECONDS: int = 5

    # ── Export Limits ────────────────────────────────────────────
    MAX_EXPORT_RANGE_DAYS: int = 30
    MAX_ACTIVE_EXPORT_JOBS: int = 10
    MIN_RECORDS_PER_DAY: int = 1
    MAX_RECORDS_PER_DAY: int = 5
    MAX_RECORDS_PER_EXPORT: int = 10_000

    # ── Request ID ───────────────────────────────────────────────
    MAX_REQUEST_ID_LENGTH: int = 100

    # ── Validators ───────────────────────────────────────────────

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        import os

        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql://", 1)
            if "VERCEL" in os.environ and v.startswith("sqlite:///./"):
                return "sqlite:////tmp/marketo_simulator.db"
        return v

    @field_validator("MIN_RECORDS_PER_DAY")
    @classmethod
    def min_records_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("MIN_RECORDS_PER_DAY must be >= 0")
        return v

    @field_validator("MAX_EXPORT_RANGE_DAYS")
    @classmethod
    def max_range_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("MAX_EXPORT_RANGE_DAYS must be > 0")
        return v

    @field_validator("MAX_ACTIVE_EXPORT_JOBS")
    @classmethod
    def max_active_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("MAX_ACTIVE_EXPORT_JOBS must be > 0")
        return v

    @model_validator(mode="after")
    def cross_field_validation(self) -> Settings:
        if self.MAX_RECORDS_PER_DAY < self.MIN_RECORDS_PER_DAY:
            raise ValueError(
                "MAX_RECORDS_PER_DAY must be >= MIN_RECORDS_PER_DAY"
            )
        if self.MAX_RECORDS_PER_EXPORT < self.MAX_RECORDS_PER_DAY:
            raise ValueError(
                "MAX_RECORDS_PER_EXPORT must be >= MAX_RECORDS_PER_DAY"
            )
        return self

    @model_validator(mode="after")
    def reject_insecure_production_defaults(self) -> Settings:
        if self.APP_ENV == "production":
            if self.MOCK_CLIENT_SECRET == "change-me":
                raise ValueError(
                    "MOCK_CLIENT_SECRET must be changed from default in production"
                )
            if self.TOKEN_HASH_SECRET == "replace-with-a-long-random-value":
                raise ValueError(
                    "TOKEN_HASH_SECRET must be changed from default in production"
                )
        return self

    @property
    def is_test_env(self) -> bool:
        return self.APP_ENV in ("local", "test")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
