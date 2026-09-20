"""
TRACE-X Application Configuration.

Pydantic-settings based configuration with environment variable loading,
field validation, and weight normalization. All ML weights are auto-normalized
to sum to 1.0 at startup.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TraceXConfig(BaseSettings):
    """
    Central configuration for TRACE-X.

    Loads from environment variables and .env file. All ML weights are
    auto-normalized to sum to 1.0 at startup. Retention must be >= 1 day.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── MongoDB ──────────────────────────────────────────────
    mongo_uri: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URI.",
    )
    db_name: str = Field(
        default="trace_x",
        description="MongoDB database name.",
    )

    # ── Application Mode ────────────────────────────────────
    demo_mode: bool = Field(
        default=True,
        description="When True, connectors return synthetic data.",
    )

    # ── Privacy / Retention ─────────────────────────────────
    retention_days: int = Field(
        default=30,
        ge=1,
        description="Auto-delete investigations after N days (TTL).",
    )

    # ── ML Weights (auto-normalized to sum=1.0) ─────────────
    name_weight: float = Field(default=0.35, ge=0.0, le=1.0)
    bio_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    cross_platform_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    evidence_weight: float = Field(default=0.10, ge=0.0, le=1.0)
    conflict_penalty: float = Field(default=0.05, ge=0.0, le=1.0)

    # ── Bayesian Prior ──────────────────────────────────────
    prior_same_person: float = Field(
        default=0.3,
        gt=0.0,
        lt=1.0,
        description="Prior probability P(same_person) for Bayesian scoring.",
    )

    # ── Application ─────────────────────────────────────────
    log_level: str = Field(default="INFO")
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Comma-separated allowed CORS origins.",
    )

    # ── Auth (Phase 3+ placeholder) ─────────────────────────
    jwt_secret: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=60, ge=1)

    # ── Validators ──────────────────────────────────────────

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is a valid Python logging level name."""
        v = v.upper()
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v not in valid:
            raise ValueError(f"log_level must be one of {valid}, got '{v}'")
        return v

    @model_validator(mode="after")
    def normalize_weights(self) -> "TraceXConfig":
        """Auto-normalize ML weights so they sum to 1.0."""
        total = (
            self.name_weight
            + self.bio_weight
            + self.cross_platform_weight
            + self.evidence_weight
            + self.conflict_penalty
        )
        if total <= 0:
            raise ValueError("Sum of ML weights must be > 0.")
        if abs(total - 1.0) > 0.01:
            self.name_weight /= total
            self.bio_weight /= total
            self.cross_platform_weight /= total
            self.evidence_weight /= total
            self.conflict_penalty /= total
        return self

    # ── Derived Properties ──────────────────────────────────

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ml_weights(self) -> dict[str, float]:
        """Return ML weights as a dictionary for the engine."""
        return {
            "name": self.name_weight,
            "bio": self.bio_weight,
            "cross_platform": self.cross_platform_weight,
            "evidence": self.evidence_weight,
            "conflict_penalty": self.conflict_penalty,
        }

    @property
    def numeric_log_level(self) -> int:
        """Return the numeric logging level."""
        return getattr(logging, self.log_level, logging.INFO)


@lru_cache(maxsize=1)
def get_config() -> TraceXConfig:
    """
    Return a cached singleton configuration instance.

    The config is loaded once from environment variables / .env and
    cached for the lifetime of the process.
    """
    return TraceXConfig()
