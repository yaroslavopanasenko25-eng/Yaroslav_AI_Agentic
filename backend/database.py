"""Supabase client and common database helpers for GuardianEye."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from supabase import Client, create_client

from config import get_settings


def get_supabase_client() -> Client:
    """Return an authenticated Supabase client built from application settings.

    Raises:
        RuntimeError: When the Supabase URL or key are still placeholder values.
    """
    settings = get_settings()

    if "your-project" in settings.supabase_url or not settings.supabase_key:
        raise RuntimeError(
            "Supabase is not configured. "
            "Set SUPABASE_URL and SUPABASE_KEY in your .env file."
        )

    try:
        return create_client(settings.supabase_url, settings.supabase_key)
    except Exception as exc:
        raise RuntimeError("Unable to initialise Supabase client.") from exc


# ── Convenience helpers ───────────────────────────────────────────────────────

def upsert_rows(table: str, records: List[Dict[str, Any]], on_conflict: str = "id") -> None:
    """Upsert a list of records into *table*, merging on *on_conflict* column."""
    if not records:
        return
    try:
        get_supabase_client().table(table).upsert(records, on_conflict=on_conflict).execute()
    except Exception as exc:
        raise RuntimeError(f"Upsert into '{table}' failed.") from exc


def fetch_rows(
    table: str,
    *,
    limit: int = 500,
    order_col: str = "created_at",
    ascending: bool = False,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Fetch rows from *table* with optional filtering and ordering.

    Returns an empty list when Supabase is not yet configured (placeholder keys),
    so the app can still start and serve mock data during local development.
    """
    try:
        client = get_supabase_client()
    except RuntimeError:
        return []

    try:
        query = client.table(table).select("*").order(order_col, desc=not ascending).limit(limit)
        if filters:
            for column, value in filters.items():
                query = query.eq(column, value)
        result = query.execute()
        return result.data or []
    except Exception as exc:
        raise RuntimeError(f"Fetch from '{table}' failed.") from exc
