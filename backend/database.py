"""Supabase client initialization for GuardianEye backend services."""

from __future__ import annotations

import os
from typing import Final

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL: Final[str] = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: Final[str] = os.getenv("SUPABASE_KEY", "")


def get_supabase_client() -> Client:
    """Create and return a validated Supabase client instance.

    Raises:
        RuntimeError: If required Supabase environment variables are missing.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")

    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as exc:  # pragma: no cover - external client failure
        raise RuntimeError("Unable to initialize Supabase client.") from exc
