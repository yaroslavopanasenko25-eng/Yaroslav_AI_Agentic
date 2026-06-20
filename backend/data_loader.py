"""Alert data ingestion: fetches from alerts.in.ua and upserts into Supabase."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from config import get_settings
from database import upsert_rows


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO-8601 string into a timezone-aware datetime, or return None."""
    if not value:
        return None
    try:
        normalised = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalised)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _duration_minutes(start: Optional[datetime], end: Optional[datetime]) -> Optional[int]:
    if not start:
        return None
    finish = end or datetime.now(timezone.utc)
    return max(0, int((finish - start).total_seconds() // 60))


def fetch_alerts() -> List[Dict[str, Any]]:
    """Fetch active alerts from alerts.in.ua using the configured API key.

    The API requires the token in an ``X-API-Key`` header.
    """
    settings = get_settings()

    if not settings.alerts_api_key or "your-alerts" in settings.alerts_api_key:
        raise RuntimeError(
            "alerts.in.ua API key is not configured. "
            "Set ALERTS_API_KEY in your .env file."
        )

    headers = {"X-API-Key": settings.alerts_api_key}

    try:
        response = requests.get(
            settings.alerts_api_url,
            headers=headers,
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload: Any = response.json()
    except requests.RequestException as exc:
        raise RuntimeError("Failed to fetch alerts from alerts.in.ua.") from exc

    alerts: Any = payload.get("alerts", payload) if isinstance(payload, dict) else payload
    if not isinstance(alerts, list):
        raise RuntimeError("Unexpected response format from alerts.in.ua.")

    return [item for item in alerts if isinstance(item, dict)]


def transform_alerts(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalise raw API payloads into Supabase-ready records."""
    records: List[Dict[str, Any]] = []

    for item in raw:
        start_dt = _parse_iso(item.get("started_at") or item.get("start_time"))
        end_dt = _parse_iso(item.get("finished_at") or item.get("end_time"))

        record: Dict[str, Any] = {
            "id": item.get("id"),
            "region_id": item.get("location_uid") or item.get("region_id"),
            "region": item.get("location_title") or item.get("region", "unknown"),
            "alert_type": item.get("alert_type") or item.get("threat_type", "unknown"),
            "start_time": start_dt.isoformat() if start_dt else None,
            "end_time": end_dt.isoformat() if end_dt else None,
            "duration_minutes": _duration_minutes(start_dt, end_dt),
            "is_active": end_dt is None,
            "raw": item,
        }

        if record["id"] is not None:
            records.append(record)

    return records


def run_ingestion() -> int:
    """Fetch → transform → upsert.  Returns the number of records processed."""
    raw = fetch_alerts()
    records = transform_alerts(raw)
    upsert_rows("alerts", records)
    return len(records)


if __name__ == "__main__":
    try:
        n = run_ingestion()
        print(f"Ingested {n} alert records.")
    except Exception as exc:
        print(f"Ingestion failed: {exc}")
