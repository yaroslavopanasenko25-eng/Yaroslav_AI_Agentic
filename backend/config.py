"""Centralised application configuration loaded from environment variables.

All environment variables are defined once here.  Every other module imports
from this file вЂ” nothing else calls ``os.getenv`` directly.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from shutil import copyfile
from typing import List

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent / ".env"
_ENV_EXAMPLE = Path(__file__).resolve().parent / ".env.example"

# Placeholders used when cloning the repo without real API keys.
_DEMO_SUPABASE_URL = "https://demo-not-configured.supabase.co"
_DEMO_SUPABASE_KEY = "demo-not-configured"
_DEMO_GROK_KEY = "demo-not-configured"
_DEMO_ALERTS_KEY = "your-alerts-in-ua-token"


def _ensure_env_file() -> None:
    """Copy .env.example → .env on first run so `git clone` works out of the box."""
    if _ENV_FILE.exists() or not _ENV_EXAMPLE.exists():
        return
    copyfile(_ENV_EXAMPLE, _ENV_FILE)
    print(
        "[GuardianEye] Created backend/.env from .env.example — demo mode.\n"
        "              Add real API keys later for live alerts and Grok AI."
    )


_ensure_env_file()


class Settings(BaseSettings):
    """Application settings resolved from the .env file or the process environment."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # в”Ђв”Ђ Supabase в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    supabase_url: str = Field(
        default=_DEMO_SUPABASE_URL,
        description="Supabase project URL",
    )
    supabase_key: str = Field(
        default=_DEMO_SUPABASE_KEY,
        description="Supabase service-role or anon key",
    )

    # в”Ђв”Ђ Grok (xAI) в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    # Accepts both GROK_* and XAI_* env names (xAI console uses XAI_ prefix).
    grok_api_key: str = Field(
        default=_DEMO_GROK_KEY,
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

    # в”Ђв”Ђ alerts.in.ua в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    alerts_api_key: str = Field(
        default=_DEMO_ALERTS_KEY,
        description="alerts.in.ua API token (Authorization: Bearer)",
    )
    alerts_api_url: str = Field(
        default="https://api.alerts.in.ua/v1/alerts/active.json",
        description="alerts.in.ua active-alerts endpoint",
    )

    # ── CORS / network ────────────────────────────────────────────────────────────
    allowed_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5175",
            "http://127.0.0.1:5175",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
        ],
        description="Comma-separated list of allowed CORS origins",
    )
    cors_allow_lan: bool = Field(
        default=True,
        description="Allow browsers from private LAN IPs (192.168.x.x, 10.x.x.x, etc.)",
    )
    cors_origin_regex: str = Field(
        default=(
            r"https?://("
            r"localhost|127\.0\.0\.1"
            r"|192\.168\.\d{1,3}\.\d{1,3}"
            r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
            r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
            r")(?::\d+)?"
        ),
        description="Regex for extra CORS origins (phones/tablets on same Wi‑Fi)",
    )
    host: str = Field(
        default="0.0.0.0",
        description="Bind address — 0.0.0.0 allows other devices on the LAN",
    )
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
        if value.startswith("https://"):
            return value.rstrip("/")
        if value.startswith("http://localhost") or value.startswith("http://127.0.0.1"):
            return value.rstrip("/")
        raise ValueError("SUPABASE_URL must start with https:// (or http://localhost for local dev)")

    def is_supabase_configured(self) -> bool:
        return (
            bool(self.supabase_key)
            and self.supabase_key not in (_DEMO_SUPABASE_KEY, "your-supabase-key", "<service-role-key>")
            and "your-project" not in self.supabase_url
            and "demo-not-configured" not in self.supabase_url
        )

    def is_grok_configured(self) -> bool:
        key = self.grok_api_key or ""
        return bool(key) and key not in (_DEMO_GROK_KEY, "your-grok-api-key") and not key.startswith("xai-<")

    def is_alerts_configured(self) -> bool:
        key = self.alerts_api_key or ""
        return bool(key) and "your-alerts" not in key and "<your" not in key

    def is_demo_mode(self) -> bool:
        return not (self.is_alerts_configured() or self.is_grok_configured() or self.is_supabase_configured())

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

