"""Transform stored alert records into Analysis-page chart/table payloads."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from kyiv_time import (
    chart_bucket_key,
    chart_labels_for_period,
    format_date_kyiv,
    format_date_label_kyiv,
    format_time_kyiv,
    now_kyiv,
    now_utc,
    period_cutoff_utc,
    war_days_count,
)
from regions_data import OCCUPIED, SLUG_TO_NAME_UK, SLUG_TO_UID, slug_from_alert

Period = str  # "1h" | "1d" | "7d" | "14d" | "30d" | "1y" | "all"


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


def _is_air_raid(rec: Dict[str, Any]) -> bool:
    atype = str(rec.get("alert_type") or "")
    return "air" in atype or "raid" in atype


def _exclude_stale(rec: Dict[str, Any], period: Period) -> bool:
    """Drop occupation / obsolete oblast-level entries from short-period analytics."""
    start = _parse_dt(rec.get("start_time") or rec.get("started_at"))
    if not start:
        return True
    if period in ("30d", "1y", "all"):
        return False

    slug = _slug_from_record(rec)
    raw = rec.get("raw") if isinstance(rec.get("raw"), dict) else {}
    loc_type = str(rec.get("location_type") or raw.get("location_type") or "")
    age = now_utc() - start
    if slug in OCCUPIED and age > timedelta(hours=24):
        return True
    if loc_type == "oblast" and age > timedelta(days=2):
        return True
    if age > timedelta(days=30):
        return True
    return False


def _location_labels(rec: Dict[str, Any], slug: str) -> tuple[str, str]:
    raw = rec.get("raw") if isinstance(rec.get("raw"), dict) else {}
    location_title = (
        rec.get("location_title")
        or raw.get("location_title")
        or rec.get("region")
        or SLUG_TO_NAME_UK.get(slug, slug)
    )
    oblast = (
        rec.get("location_oblast")
        or raw.get("location_oblast")
        or SLUG_TO_NAME_UK.get(slug, "")
    )
    return str(location_title), str(oblast)


def _event_duration_minutes(rec: Dict[str, Any]) -> int:
    start = _parse_dt(rec.get("start_time") or rec.get("started_at"))
    if not start:
        return int(rec.get("duration_minutes") or 0)
    end = _parse_dt(rec.get("end_time") or rec.get("finished_at"))
    if end:
        return max(0, int((end - start).total_seconds() // 60))
    if rec.get("is_active"):
        return max(0, int((now_utc() - start).total_seconds() // 60))
    return int(rec.get("duration_minutes") or 0)


def _format_duration_minutes(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes} хв."
    hours, mins = divmod(minutes, 60)
    if mins:
        return f"{hours} год. {mins} хв."
    return f"{hours} год."


def _format_duration_seconds(total_seconds: int) -> str:
    if total_seconds < 60:
        return f"{total_seconds} с."
    minutes, seconds = divmod(total_seconds, 60)
    if minutes < 60:
        if seconds:
            return f"{minutes} хв. {seconds} с."
        return f"{minutes} хв."
    hours, rem = divmod(minutes, 60)
    if rem:
        return f"{hours} год. {rem} хв."
    return f"{hours} год."


def _to_alarm_event(rec: Dict[str, Any]) -> Dict[str, Any]:
    start = _parse_dt(rec.get("start_time") or rec.get("started_at"))
    end = _parse_dt(rec.get("end_time") or rec.get("finished_at"))
    duration = rec.get("duration_minutes")
    if duration is None and start:
        finish = end or now_utc()
        duration = max(0, int((finish - start).total_seconds() // 60))

    alert_type = str(rec.get("alert_type") or "air_raid")
    slug = _slug_from_record(rec)
    location_title, oblast = _location_labels(rec, slug)
    is_active = bool(rec.get("is_active", end is None))
    if is_active and start:
        duration_seconds = max(0, int((now_utc() - start).total_seconds()))
        duration_int = duration_seconds // 60
        duration_label = _format_duration_seconds(duration_seconds)
    else:
        duration_int = int(duration or 0)
        duration_label = _format_duration_minutes(duration_int)

    return {
        "id": str(rec.get("id", "")),
        "date": format_date_kyiv(start),
        "dateLabel": format_date_label_kyiv(start),
        "startTime": format_time_kyiv(start),
        "timezone": "Europe/Kyiv",
        "duration": duration_int,
        "durationLabel": duration_label,
        "regions": [slug] if slug else [],
        "regionLabel": location_title,
        "oblastLabel": oblast,
        "alertType": alert_type,
        "isActive": is_active,
        "threats": [
            {
                "type": "missiles" if _is_air_raid(rec) else "drones",
                "total": 1,
                "destroyed": 0,
                "hit": 0,
                "lost": 0,
            }
        ],
    }


def _filter_for_period(
    records: List[Dict[str, Any]],
    period: Period,
    cutoff: datetime,
) -> List[Dict[str, Any]]:
    seen: set[str] = set()
    filtered: List[Dict[str, Any]] = []
    for rec in records:
        rid = str(rec.get("id") or "")
        if rid and rid in seen:
            continue
        start = _parse_dt(rec.get("start_time") or rec.get("started_at"))
        if not start or start < cutoff:
            continue
        if _slug_from_record(rec) not in SLUG_TO_UID:
            continue
        if _exclude_stale(rec, period):
            continue
        if rid:
            seen.add(rid)
        filtered.append(rec)
    return filtered


def _apply_live_overlay(
    records: List[Dict[str, Any]],
    live_records: Optional[List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Prefer fresh live API fields; clear stale is_active on archived copies."""
    if not live_records:
        return records
    live_by_id = {str(r["id"]): r for r in live_records if r.get("id") is not None}
    merged: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for rec in records:
        rid = str(rec.get("id") or "")
        if rid and rid in live_by_id:
            merged.append(live_by_id[rid])
        else:
            stale = dict(rec)
            stale["is_active"] = False
            merged.append(stale)
        if rid:
            seen.add(rid)
    for rec in live_records:
        rid = str(rec.get("id") or "")
        if rid and rid not in seen:
            merged.append(rec)
            seen.add(rid)
    return merged


def _count_active_air_raids(live_records: Optional[List[Dict[str, Any]]]) -> int:
    """Currently active air-raid alerts from live API only (matches dashboard semantics)."""
    if not live_records:
        return 0
    seen: set[str] = set()
    count = 0
    for rec in live_records:
        if not rec.get("is_active") or not _is_air_raid(rec):
            continue
        if _slug_from_record(rec) not in SLUG_TO_UID:
            continue
        rid = str(rec.get("id") or "")
        if rid:
            if rid in seen:
                continue
            seen.add(rid)
        count += 1
    return count


def build_analysis_payload(
    records: List[Dict[str, Any]],
    period: Period = "14d",
    *,
    live_records: Optional[List[Dict[str, Any]]] = None,
    war_bar_data: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Aggregate alert history into chart + table structures for the frontend."""
    cutoff = period_cutoff_utc(period)
    source = _apply_live_overlay(records, live_records)

    filtered = _filter_for_period(source, period, cutoff)
    filtered_air = [r for r in filtered if _is_air_raid(r)]
    chart_rows = filtered_air if filtered_air else filtered

    by_day: Dict[str, Dict[str, int]] = defaultdict(lambda: {"air_raid": 0, "other": 0})
    for rec in chart_rows:
        start = _parse_dt(rec.get("start_time") or rec.get("started_at"))
        if not start:
            continue
        day_key = chart_bucket_key(start, period)
        if _is_air_raid(rec):
            by_day[day_key]["air_raid"] += 1
        else:
            by_day[day_key]["other"] += 1

    bar_data = [
        {
            "date": day,
            "missiles": by_day[day]["air_raid"],
            "drones": by_day[day]["other"],
            "destroyed": 0,
        }
        for day in chart_labels_for_period(period)
    ]
    if period in ("all", "1y") and war_bar_data:
        by_date = {row["date"]: dict(row) for row in war_bar_data}
        for day in chart_labels_for_period(period):
            rec = by_day.get(day, {"air_raid": 0, "other": 0})
            row = by_date.setdefault(day, {"date": day, "missiles": 0, "drones": 0, "destroyed": 0})
            row["missiles"] = max(row["missiles"], rec["air_raid"])
            row["drones"] = max(row["drones"], rec["other"])
        bar_data = [by_date[day] for day in chart_labels_for_period(period)]

    line_by_day: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"duration": 0, "regions": set(), "count": 0})
    for rec in chart_rows:
        start = _parse_dt(rec.get("start_time") or rec.get("started_at"))
        if not start:
            continue
        day_key = chart_bucket_key(start, period)
        dur = min(_event_duration_minutes(rec), 24 * 60)
        line_by_day[day_key]["duration"] += dur
        line_by_day[day_key]["regions"].add(_slug_from_record(rec))
        line_by_day[day_key]["count"] += 1

    if period in ("all", "1y") and war_bar_data:
        line_data = []
        for row in bar_data:
            day = row["date"]
            threats = row["missiles"] + row["drones"]
            bucket = line_by_day.get(day, {"duration": 0, "regions": set(), "count": 0})
            count = max(bucket["count"], 1)
            line_data.append({
                "date": day,
                "duration": int(bucket["duration"] / count) if bucket["count"] else 0,
                "regions": len(bucket["regions"]),
                "threats": threats or bucket["count"],
            })
        if not any(r["threats"] for r in line_data):
            line_data = [
                {
                    "date": day,
                    "duration": int(line_by_day[day]["duration"] / max(line_by_day[day]["count"], 1)),
                    "regions": len(line_by_day[day]["regions"]),
                    "threats": line_by_day[day]["count"],
                }
                for day in chart_labels_for_period(period)
            ]
    else:
        line_data = [
            {
                "date": day,
                "duration": int(line_by_day[day]["duration"] / max(line_by_day[day]["count"], 1)),
                "regions": len(line_by_day[day]["regions"]),
                "threats": line_by_day[day]["count"],
            }
            for day in chart_labels_for_period(period)
        ]

    table_rows = sorted(filtered_air, key=lambda r: r.get("start_time") or "", reverse=True)
    active_count = _count_active_air_raids(live_records)

    period_durations = [
        _event_duration_minutes(r) for r in filtered_air if _event_duration_minutes(r) <= 24 * 60
    ]
    avg_duration = int(sum(period_durations) / max(len(period_durations), 1)) if period_durations else 0

    air_count = len(filtered_air)
    totals = {
        "missiles": air_count,
        "drones": len(filtered) - air_count,
        "destroyed": 0,
        "hit": 0,
        "totalAlerts": air_count,
        "activeAlerts": active_count,
        "avgDurationMinutes": avg_duration,
        "regionsAffected": len({_slug_from_record(r) for r in filtered_air}),
    }

    return {
        "barData": bar_data,
        "lineData": line_data,
        "history": [_to_alarm_event(r) for r in table_rows[:50]],
        "totals": totals,
        "updatedAt": now_kyiv().strftime("%H:%M:%S"),
        "source": "live",
        "warDays": war_days_count() if period == "all" else None,
        "periodDays": _period_days(period),
    }


def _period_days(period: Period) -> int:
    mapping = {"1h": 0, "1d": 1, "7d": 7, "14d": 14, "30d": 30, "1y": 365, "all": war_days_count()}
    return mapping.get(period, 14)
