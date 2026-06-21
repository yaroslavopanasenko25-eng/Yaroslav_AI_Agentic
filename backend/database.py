"""Supabase client and common database helpers for GuardianEye."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from supabase import Client, create_client

from config import get_settings


def get_supabase_client() -> Client:
    """Return an authenticated Supabase client built from application settings."""
    settings = get_settings()

    if "your-project" in settings.supabase_url or not settings.supabase_key:
        raise RuntimeError(
            "Supabase is not configured. "
            "Set SUPABASE_URL and SUPABASE_KEY in your .env file."
        )

    try:
        return create_client(settings.supabase_url, settings.supabase_key)
    except Exception as exc:  # pragma: no cover - external client failure
        raise RuntimeError("Unable to initialize Supabase client.") from exc


def fetch_rows(
    table: str,
    *,
    limit: Optional[int] = None,
    order_col: Optional[str] = None,
    ascending: bool = True,
    since_iso: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetch rows from a Supabase table with optional ordering and time filter."""
    client = get_supabase_client()
    query = client.table(table).select("*")

    if since_iso and order_col:
        query = query.gte(order_col, since_iso)
    if order_col:
        query = query.order(order_col, desc=not ascending)
    if limit is not None:
        query = query.limit(limit)

    result = query.execute()
    return list(result.data or [])


def upsert_rows(table: str, rows: List[Dict[str, Any]], *, on_conflict: str = "id") -> int:
    """Upsert rows into a Supabase table. Returns number of rows attempted."""
    if not rows:
        return 0
    client = get_supabase_client()
    client.table(table).upsert(rows, on_conflict=on_conflict).execute()
    return len(rows)
