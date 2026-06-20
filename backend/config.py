"""Centralised application configuration loaded from environment variables.

All environment variables are defined once here.  Every other module imports
from this file — nothing else calls ``os.getenv`` directly.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings resolved from the .env file or the process environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Supabase ─────────────────────────────────────────────────────────────
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase service-role or anon key")

    # ── Grok (xAI) ───────────────────────────────────────────────────────────
    grok_api_key: str = Field(..., description="xAI Grok API key")
    grok_api_url: str = Field(
        default="https://api.x.ai/v1/chat/completions",
        description="Grok chat completions endpoint",
    )
    grok_model: str = Field(
        default="grok-3-mini",
        description="Grok model identifier",
    )

    # ── alerts.in.ua ─────────────────────────────────────────────────────────
    alerts_api_key: str = Field(..., description="alerts.in.ua API token (X-API-Key header)")
    alerts_api_url: str = Field(
        default="https://api.alerts.in.ua/v1/alerts/active.json",
        description="alerts.in.ua active-alerts endpoint",
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Comma-separated list of allowed CORS origins",
    )

    # ── General ──────────────────────────────────────────────────────────────
    debug: bool = Field(default=False, description="Enable debug logging")
    request_timeout_seconds: int = Field(
        default=20,
        ge=1,
        description="Default outbound HTTP request timeout in seconds",
    )

    @field_validator("supabase_url")
    @classmethod
    def _validate_supabase_url(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("SUPABASE_URL must start with https://")
        return value.rstrip("/")

    @field_validator("grok_api_url")
    @classmethod
    def _validate_grok_url(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("GROK_API_URL must start with https://")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance.

    Use this function everywhere instead of constructing ``Settings()`` directly
    so the .env file is only parsed once per process.
    """
    return Settings()
