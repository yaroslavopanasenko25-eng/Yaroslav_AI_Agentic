"""Transform stored alert records into Analysis-page chart/table payloads."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from regions_data import SLUG_TO_NAME_UK, SLUG_TO_UID, slug_from_alert

Period = str  # "1h" | "1d" | "7d" | "14d" | "30d" | "all"

_PERIOD_DAYS: Dict[Period, int] = {
    "1h": 0,
    "1d": 1,
    "7d": 7,
    "14d": 14,
    "30d": 30,
    "all": 60,
}


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _slug_from_record(rec: Dict[str, Any]) -> str:
    slug = str(rec.get("region_slug") or "")
    if slug in SLUG_TO_UID:
        return slug
    raw = rec.get("raw")
    if isinstance(raw, dict):
        slug = slug_from_alert(raw)
        if slug in SLUG_TO_UID:
            return slug
    return ""


def _to_alarm_event(rec: Dict[str, Any]) -> Dict[str, Any]:
    start = _parse_dt(rec.get("start_time") or rec.get("started_at"))
    end = _parse_dt(rec.get("end_time") or rec.get("finished_at"))
    duration = rec.get("duration_minutes")
    if duration is None and start:
        finish = end or datetime.now(timezone.utc)
        duration = max(0, int((finish - start).total_seconds() // 60))

    alert_type = str(rec.get("alert_type") or "air_raid")
    slug = _slug_from_record(rec)
    region_name = SLUG_TO_NAME_UK.get(slug, rec.get("region", slug))

    return {
        "id": str(rec.get("id", "")),
        "date": (start.date().isoformat() if start else ""),
        "startTime": start.strftime("%H:%M") if start else "—",
        "duration": int(duration or 0),
        "regions": [slug] if slug else [],
        "regionLabel": region_name,
        "alertType": alert_type,
        "threats": [
            {
                "type": "missiles" if "rocket" in alert_type or "missile" in alert_type else "drones",
                "total": 1,
                "destroyed": 0,
                "hit": 0,
                "lost": 0,
            }
        ],
    }


def build_analysis_payload(
    records: List[Dict[str, Any]],
    period: Period = "14d",
) -> Dict[str, Any]:
    """Aggregate alert history into chart + table structures for the frontend."""
    days = _PERIOD_DAYS.get(period, 14)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days if period != "1h" else 0)

    filtered: List[Dict[str, Any]] = []
    for rec in records:
        start = _parse_dt(rec.get("start_time") or rec.get("started_at"))
        if not start:
            continue
        if period == "1h":
            if start < datetime.now(timezone.utc) - timedelta(hours=1):
                continue
        elif start < cutoff:
            continue
        filtered.append(rec)

    # Drop records we cannot map to an oblast (old bad cache entries)
    filtered = [r for r in filtered if _slug_from_record(r) in SLUG_TO_UID]

    # ── Daily bar chart: alert counts by type ─────────────────────────────────
    by_day: Dict[str, Dict[str, int]] = defaultdict(lambda: {"air_raid": 0, "other": 0, "total": 0})
    for rec in filtered:
        start = _parse_dt(rec.get("start_time") or rec.get("started_at"))
        if not start:
            continue
        day_key = start.strftime("%m.%d") if period in ("7d", "14d", "30d", "all") else start.strftime("%H:%M")
        atype = str(rec.get("alert_type") or "air_raid")
        bucket = "air_raid" if "air" in atype or "raid" in atype else "other"
        by_day[day_key][bucket] += 1
        by_day[day_key]["total"] += 1

    bar_data = [
        {
            "date": day,
            "missiles": counts["air_raid"],
            "drones": counts["other"],
            "destroyed": 0,
        }
        for day, counts in sorted(by_day.items())
    ]

    # ── Line chart: duration + unique regions per day ─────────────────────────
    line_by_day: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"duration": 0, "regions": set(), "count": 0})
    for rec in filtered:
        start = _parse_dt(rec.get("start_time") or rec.get("started_at"))
        if not start:
            continue
        day_key = start.strftime("%m.%d") if period in ("7d", "14d", "30d", "all") else start.strftime("%H:%M")
        dur = rec.get("duration_minutes")
        if dur is None:
            end = _parse_dt(rec.get("end_time") or rec.get("finished_at"))
            if end:
                dur = max(0, int((end - start).total_seconds() // 60))
        line_by_day[day_key]["duration"] += int(dur or 0)
        line_by_day[day_key]["regions"].add(_slug_from_record(rec))
        line_by_day[day_key]["count"] += 1

    line_data = [
        {
            "date": day,
            "duration": int(v["duration"] / max(v["count"], 1)),
            "regions": len(v["regions"]),
            "threats": v["count"],
        }
        for day, v in sorted(line_by_day.items())
    ]

    history = [_to_alarm_event(r) for r in sorted(
        filtered,
        key=lambda r: r.get("start_time") or "",
        reverse=True,
    )[:50]]

    totals = {
        "missiles": sum(b["missiles"] for b in bar_data),
        "drones": sum(b["drones"] for b in bar_data),
        "destroyed": 0,
        "hit": 0,
        "totalAlerts": len(filtered),
    }

    return {
        "barData": bar_data,
        "lineData": line_data,
        "history": history,
        "totals": totals,
        "source": "live",
    }
