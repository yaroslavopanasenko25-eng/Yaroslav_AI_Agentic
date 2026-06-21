"""Centralised application configuration loaded from environment variables.

All environment variables are defined once here.  Every other module imports
from this file — nothing else calls ``os.getenv`` directly.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent / ".env"


class Settings(BaseSettings):
    """Application settings resolved from the .env file or the process environment."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Supabase ─────────────────────────────────────────────────────────────
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase service-role or anon key")

    # ── Grok (xAI) ───────────────────────────────────────────────────────────
    # Accepts both GROK_* and XAI_* env names (xAI console uses XAI_ prefix).
    grok_api_key: str = Field(
        ...,
        validation_alias=AliasChoices("GROK_API_KEY", "XAI_API_KEY"),
        description="xAI Grok API key",
    )
    grok_api_url: str = Field(
        default="https://api.x.ai/v1/chat/completions",
        validation_alias=AliasChoices("GROK_API_URL", "XAI_API_URL"),
        description="Grok chat completions endpoint",
    )
    grok_model: str = Field(
        default="grok-3-mini",
        validation_alias=AliasChoices("GROK_MODEL", "XAI_MODEL"),
        description="Grok model identifier",
    )
    xai_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("XAI_BASE_URL", "GROK_BASE_URL"),
        description="Optional xAI base URL; /chat/completions is appended automatically",
    )

    # ── alerts.in.ua ─────────────────────────────────────────────────────────
    alerts_api_key: str = Field(..., description="alerts.in.ua API token (Authorization: Bearer)")
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
    port: int = Field(default=8080, ge=1, le=65535, description="Server port (Docker/DO)")
    shelters_json_path: str | None = Field(
        default=None,
        description="Override path to shelters.json (Docker production)",
    )
    request_timeout_seconds: int = Field(
        default=20,
        ge=1,
        description="Default outbound HTTP request timeout in seconds",
    )
    alerts_poll_interval_seconds: int = Field(
        default=30,
        ge=15,
        le=120,
        description="Background poll interval for alerts.in.ua active.json (min 15s)",
    )
    alert_store_path: str | None = Field(
        default=None,
        description="Override path for local alert history JSON store",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _parse_allowed_origins(cls, value: object) -> List[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value  # type: ignore[return-value]

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

    @model_validator(mode="after")
    def _normalize_xai_settings(self) -> "Settings":
        """Build the completions URL from XAI_BASE_URL when only a base is provided."""
        if self.xai_base_url:
            base = self.xai_base_url.rstrip("/")
            default_url = "https://api.x.ai/v1/chat/completions"
            if self.grok_api_url == default_url or not self.grok_api_url.endswith("/chat/completions"):
                object.__setattr__(self, "grok_api_url", f"{base}/chat/completions")
        return self

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Prefer .env file over stale OS-level placeholders (e.g. GROK_API_KEY=your-grok-api-key).
        return init_settings, dotenv_settings, env_settings, file_secret_settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance.

    Use this function everywhere instead of constructing ``Settings()`` directly
    so the .env file is only parsed once per process.
    """
    return Settings()
