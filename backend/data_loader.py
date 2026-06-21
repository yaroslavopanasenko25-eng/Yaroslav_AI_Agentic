"""Alert data ingestion: fetches from alerts.in.ua and upserts into Supabase."""

from __future__ import annotations

from datetime import datetime, timezone

from kyiv_time import now_utc
from typing import Any, Dict, List, Optional

from alerts_service import get_alerts_service
from config import get_settings
from database import upsert_rows
from regions_data import API_OBLAST_UID_TO_SLUG, slug_from_alert


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
    finish = end or now_utc()
    return max(0, int((finish - start).total_seconds() // 60))


def fetch_alerts() -> List[Dict[str, Any]]:
    """Return cached active alerts (refresh if needed)."""
    svc = get_alerts_service()
    svc.refresh_active()
    return svc.get_alerts()


def transform_alerts(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalise raw API payloads into store/Supabase-ready records."""
    records: List[Dict[str, Any]] = []

    for item in raw:
        start_dt = _parse_iso(item.get("started_at") or item.get("start_time"))
        end_dt = _parse_iso(item.get("finished_at") or item.get("end_time"))
        oblast_slug = slug_from_alert(item)
        region_id = str(item.get("location_oblast_uid") or item.get("location_uid") or "")

        record: Dict[str, Any] = {
            "id": str(item.get("id")),
            "region_id": region_id,
            "region_slug": oblast_slug,
            "region": item.get("location_oblast") or item.get("location_title") or "unknown",
            "location_title": item.get("location_title") or "",
            "location_oblast": item.get("location_oblast") or "",
            "location_type": item.get("location_type") or "",
            "alert_type": item.get("alert_type") or item.get("threat_type", "unknown"),
            "start_time": start_dt.isoformat() if start_dt else None,
            "end_time": end_dt.isoformat() if end_dt else None,
            "duration_minutes": _duration_minutes(start_dt, end_dt),
            "is_active": end_dt is None,
            "raw": item,
        }

        if record["id"] and record["id"] != "None":
            records.append(record)

    return records


def run_ingestion() -> int:
    """Fetch → transform → upsert.  Returns the number of records processed."""
    raw = fetch_alerts()
    records = transform_alerts(raw)
    if not records:
        return 0

    from alert_store import upsert_alerts

    upsert_alerts(records)

    settings = get_settings()
    if settings.is_supabase_configured():
        upsert_rows("alerts", records)

    return len(records)


if __name__ == "__main__":
    try:
        n = run_ingestion()
        print(f"Ingested {n} alert records.")
    except Exception as exc:
        print(f"Ingestion failed: {exc}")
