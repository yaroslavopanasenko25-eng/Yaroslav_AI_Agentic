"""Data loader scaffold for ingesting Ukraine alert data into Supabase."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from database import get_supabase_client

ALERTS_API_URL: str = os.getenv("ALERTS_API_URL", "https://api.alerts.in.ua/v1/alerts/active.json")
REQUEST_TIMEOUT_SECONDS: int = 15


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO8601 datetime string into a timezone-aware datetime object."""
    if not value:
        return None

    try:
        normalized_value: str = value.replace("Z", "+00:00")
        parsed: datetime = datetime.fromisoformat(normalized_value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _compute_duration_minutes(start_time: Optional[datetime], end_time: Optional[datetime]) -> Optional[int]:
    """Compute alert duration in minutes from start and end timestamps."""
    if not start_time:
        return None

    end: datetime = end_time or datetime.now(timezone.utc)
    total_minutes: int = int((end - start_time).total_seconds() // 60)
    return max(total_minutes, 0)


def fetch_alerts() -> List[Dict[str, Any]]:
    """Fetch raw alert payloads from alerts-in-ua API endpoint."""
    try:
        response: requests.Response = requests.get(ALERTS_API_URL, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload: Any = response.json()
    except requests.RequestException as exc:
        raise RuntimeError("Failed to fetch alert data from external API.") from exc

    if isinstance(payload, dict):
        alerts: Any = payload.get("alerts", [])
    else:
        alerts = payload

    if not isinstance(alerts, list):
        raise RuntimeError("Unexpected alerts payload format: expected list.")

    return [item for item in alerts if isinstance(item, dict)]


def transform_alerts(raw_alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform external alert payloads into database-ready records."""
    records: List[Dict[str, Any]] = []

    for item in raw_alerts:
        start_dt: Optional[datetime] = _parse_iso_datetime(item.get("start_time"))
        end_dt: Optional[datetime] = _parse_iso_datetime(item.get("end_time"))

        record: Dict[str, Any] = {
            "id": item.get("id"),
            "start_time": start_dt.isoformat() if start_dt else None,
            "end_time": end_dt.isoformat() if end_dt else None,
            "duration": _compute_duration_minutes(start_dt, end_dt),
            "region": item.get("region", "unknown"),
            "threat_type": item.get("threat_type", "unknown"),
            "risk_level": item.get("risk_level", "medium"),
        }

        if record["id"] is not None:
            records.append(record)

    return records


def upsert_alerts(records: List[Dict[str, Any]]) -> None:
    """Upsert transformed alert records into the Supabase `alerts` table."""
    if not records:
        return

    try:
        supabase_client = get_supabase_client()
        supabase_client.table("alerts").upsert(records).execute()
    except Exception as exc:  # pragma: no cover - external DB failure
        raise RuntimeError("Failed to upsert alert records into Supabase.") from exc


def run_data_loader() -> int:
    """Run complete ingestion flow and return number of upserted records."""
    raw_alerts: List[Dict[str, Any]] = fetch_alerts()
    transformed: List[Dict[str, Any]] = transform_alerts(raw_alerts)
    upsert_alerts(transformed)
    return len(transformed)


if __name__ == "__main__":
    try:
        loaded_count: int = run_data_loader()
        print(f"Successfully processed and upserted {loaded_count} alert records.")
    except Exception as exc:
        print(f"Data loader execution failed: {exc}")
