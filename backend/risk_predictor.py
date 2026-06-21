"""Statistical risk analysis from stored alert history for RAG / prediction."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

from alert_store import fetch_history
from kyiv_time import now_kyiv, now_utc, to_kyiv
from regions_data import SLUG_TO_NAME_UK, SLUG_TO_NAME_EN

_WEEKDAY_UK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
_WEEKDAY_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

_DISCLAIMER_UK = (
    "Це статистична оцінка на основі минулих тривог alerts.in.ua, не офіційний прогноз. "
    "Завжди реагуйте на офіційну тривогу в додатку."
)
_DISCLAIMER_EN = (
    "Statistical estimate from past alerts.in.ua data, not an official forecast. "
    "Always respond to official alarms in the app."
)


def _parse_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _region_slug(rec: Dict[str, Any]) -> str:
    slug = str(rec.get("region_slug") or rec.get("region") or "")
    if slug in SLUG_TO_NAME_UK:
        return slug
    return slug.lower().replace(" ", "-")


def _load_frame(days: int = 30, region_slug: Optional[str] = None) -> pd.DataFrame:
    since = (now_utc() - timedelta(days=days)).isoformat()
    rows = fetch_history(since_iso=since, limit=None)
    if not rows:
        rows = fetch_history(limit=5000)

    records: List[Dict[str, Any]] = []
    for rec in rows:
        start = _parse_dt(rec.get("start_time") or rec.get("started_at"))
        if not start:
            continue
        slug = _region_slug(rec)
        if region_slug and slug != region_slug:
            continue
        kyiv = to_kyiv(start)
        records.append({
            "start_time": start,
            "hour": kyiv.hour,
            "weekday": kyiv.weekday(),
            "region_slug": slug,
            "duration_minutes": int(rec.get("duration_minutes") or 0),
        })

    if not records:
        return pd.DataFrame(columns=["start_time", "hour", "weekday", "region_slug", "duration_minutes"])
    return pd.DataFrame(records)


def _risk_level_from_probability(prob: float) -> str:
    if prob >= 70:
        return "high"
    if prob >= 40:
        return "medium"
    if prob >= 15:
        return "low"
    return "minimal"


def compute_risk_brief(
    region_slug: str,
    *,
    current_status: str = "clear",
    language: str = "uk",
) -> Dict[str, Any]:
    """Build structured risk summary for one oblast."""
    is_uk = language == "uk"
    frame = _load_frame(days=30, region_slug=region_slug)
    name = SLUG_TO_NAME_UK.get(region_slug, region_slug) if is_uk else SLUG_TO_NAME_EN.get(region_slug, region_slug)

    brief: Dict[str, Any] = {
        "region_slug": region_slug,
        "region_name": name,
        "current_status": current_status,
        "active_now": current_status == "active",
        "total_30d": int(len(frame)),
        "disclaimer": _DISCLAIMER_UK if is_uk else _DISCLAIMER_EN,
    }

    if frame.empty:
        brief["risk_level"] = "unknown"
        brief["next_6h_probability"] = None
        brief["peak_hours"] = []
        brief["peak_weekdays"] = []
        brief["recent_events"] = []
        brief["avg_duration_minutes"] = 0
        return brief

    hour_counts = Counter(frame["hour"].tolist())
    dow_counts = Counter(frame["weekday"].tolist())
    peak_hours = [h for h, _ in hour_counts.most_common(3)]
    peak_dow_idx = [d for d, _ in dow_counts.most_common(2)]
    weekdays = _WEEKDAY_UK if is_uk else _WEEKDAY_EN
    peak_weekdays = [weekdays[d] for d in peak_dow_idx if 0 <= d < 7]

    brief["peak_hours"] = [f"{h:02d}:00" for h in peak_hours]
    brief["peak_weekdays"] = peak_weekdays
    brief["avg_duration_minutes"] = int(frame["duration_minutes"].mean())

    # Recent event labels
    recent = frame.sort_values("start_time", ascending=False).head(5)
    recent_events: List[str] = []
    for _, row in recent.iterrows():
            dt = row["start_time"]
            if hasattr(dt, "astimezone"):
                dt = to_kyiv(dt)
                recent_events.append(dt.strftime("%d.%m %H:%M"))
    brief["recent_events"] = recent_events

    # Next-6h probability heuristic
    now = now_kyiv()
    current_hour = now.hour
    upcoming_hours = [(current_hour + i) % 24 for i in range(6)]
    total = len(frame)
    hour_totals = defaultdict(int, hour_counts)
    window_hits = sum(hour_totals.get(h, 0) for h in upcoming_hours)
    # Normalize: expected share if uniform = 6/24 of events
    expected = total * (6 / 24) if total else 0
    if expected > 0:
        ratio = window_hits / expected
        prob = min(95, max(5, int(ratio * 35)))
    else:
        prob = 10

    # Boost if current hour is historically peak
    if current_hour in peak_hours[:2]:
        prob = min(95, prob + 20)

    # Live status overrides
    if current_status == "active":
        prob = 95
    elif current_status == "warning":
        prob = min(95, prob + 25)

    brief["next_6h_probability"] = prob
    brief["risk_level"] = _risk_level_from_probability(prob)
    return brief


def format_risk_section(brief: Dict[str, Any], *, language: str = "uk") -> str:
    """Human-readable risk block for agent context."""
    if not brief:
        return ""

    is_uk = language == "uk"
    lines = [
        "## Статистичний прогноз тривог" if is_uk else "## Statistical alarm forecast",
        f"{'Область' if is_uk else 'Oblast'}: {brief.get('region_name', '?')}",
        f"{'Записів за 30 днів' if is_uk else 'Records (30d)'}: {brief.get('total_30d', 0)}",
    ]

    prob = brief.get("next_6h_probability")
    if prob is not None:
        level = brief.get("risk_level", "?")
        lines.append(
            f"{'Ймовірність тривоги (6 год)' if is_uk else 'Alarm probability (6h)'}: {prob}% ({level})"
        )

    if brief.get("peak_hours"):
        lines.append(
            f"{'Пікові години' if is_uk else 'Peak hours'}: {', '.join(brief['peak_hours'])}"
        )
    if brief.get("peak_weekdays"):
        lines.append(
            f"{'Пікові дні' if is_uk else 'Peak days'}: {', '.join(brief['peak_weekdays'])}"
        )
    if brief.get("avg_duration_minutes"):
        lines.append(
            f"{'Сер. тривалість' if is_uk else 'Avg duration'}: {brief['avg_duration_minutes']} "
            f"{'хв' if is_uk else 'min'}"
        )
    if brief.get("recent_events"):
        lines.append(("Останні тривоги: " if is_uk else "Recent alarms: ") + "; ".join(brief["recent_events"]))

    lines.append(brief.get("disclaimer", ""))
    return "\n".join(lines)


def regional_ranking(*, language: str = "uk", top_n: int = 5) -> List[Dict[str, Any]]:
    """Rank oblasts by 30-day alert count for dispatcher overview."""
    frame = _load_frame(days=30)
    if frame.empty:
        return []
    counts = frame.groupby("region_slug").size().sort_values(ascending=False).head(top_n)
    names = SLUG_TO_NAME_UK if language == "uk" else SLUG_TO_NAME_EN
    return [
        {"region_slug": slug, "region_name": names.get(slug, slug), "count_30d": int(count)}
        for slug, count in counts.items()
    ]
