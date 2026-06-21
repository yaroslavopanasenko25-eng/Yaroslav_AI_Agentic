"""Kyiv (Europe/Kyiv) timezone helpers — all user-facing times use this zone."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

KYIV_TZ = ZoneInfo("Europe/Kyiv")

# Full-scale invasion start (Kyiv time) — used for the «Вся війна» / all period
WAR_START_KYIV = datetime(2022, 2, 24, 0, 0, 0, tzinfo=KYIV_TZ)


def now_kyiv() -> datetime:
    return datetime.now(KYIV_TZ)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_kyiv(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(KYIV_TZ)


def kyiv_midnight_utc(ref: datetime | None = None) -> datetime:
    """UTC instant of 00:00 on the Kyiv calendar day for *ref* (default: today in Kyiv)."""
    local = to_kyiv(ref or now_utc()).replace(hour=0, minute=0, second=0, microsecond=0)
    return local.astimezone(timezone.utc)


def war_start_utc() -> datetime:
    return WAR_START_KYIV.astimezone(timezone.utc)


def war_days_count() -> int:
    """Calendar days since full-scale invasion (inclusive of start day, Kyiv time)."""
    return (now_kyiv().date() - WAR_START_KYIV.date()).days + 1


def period_cutoff_utc(period: str) -> datetime:
    """Earliest UTC instant included for the given analysis period (Kyiv calendar where relevant)."""
    if period == "1h":
        return now_utc() - timedelta(hours=1)
    if period == "1d":
        return kyiv_midnight_utc()
    if period == "all":
        return war_start_utc()
    if period == "1y":
        return kyiv_midnight_utc(now_utc() - timedelta(days=365))
    days = {"7d": 7, "14d": 14, "30d": 30}.get(period, 14)
    return kyiv_midnight_utc(now_utc() - timedelta(days=days))


def format_time_kyiv(dt: datetime | None) -> str:
    if not dt:
        return "—"
    return to_kyiv(dt).strftime("%H:%M")


def format_date_kyiv(dt: datetime | None) -> str:
    if not dt:
        return ""
    return to_kyiv(dt).strftime("%Y-%m-%d")


def format_date_label_kyiv(dt: datetime | None, *, today_uk: str = "Сьогодні", today_en: str = "Today") -> str:
    """Human date label; callers pass localized 'today' string via startDateLabel instead."""
    if not dt:
        return ""
    local = to_kyiv(dt)
    if local.date() == now_kyiv().date():
        return today_uk
    return local.strftime("%d.%m.%Y")


def floor_to_5min_kyiv(dt: datetime | None = None) -> datetime:
    """Round a Kyiv datetime down to the nearest 5-minute mark."""
    local = to_kyiv(dt) if dt is not None else now_kyiv()
    return local.replace(minute=(local.minute // 5) * 5, second=0, microsecond=0)


def _month_labels_from(start: datetime, end: datetime) -> list[str]:
    labels: list[str] = []
    cursor = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_month = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    while cursor <= end_month:
        labels.append(cursor.strftime("%m.%y"))
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)
    return labels


def chart_labels_for_period(period: str) -> list[str]:
    """X-axis bucket labels aligned with chart_bucket_key()."""
    if period == "1h":
        end = floor_to_5min_kyiv()
        return [(end - timedelta(minutes=5 * i)).strftime("%H:%M") for i in range(11, -1, -1)]
    if period == "1d":
        return [f"{h:02d}:00" for h in range(24)]
    if period == "all":
        return _month_labels_from(WAR_START_KYIV, now_kyiv())
    if period == "1y":
        start = now_kyiv() - timedelta(days=365)
        return _month_labels_from(start.replace(day=1), now_kyiv())
    days_map = {"7d": 7, "14d": 14, "30d": 30}
    count = days_map.get(period, 14)
    today = now_kyiv().date()
    return [(today - timedelta(days=offset)).strftime("%m.%d") for offset in range(count - 1, -1, -1)]


def chart_bucket_key(dt: datetime, period: str) -> str:
    local = to_kyiv(dt)
    if period == "1h":
        return floor_to_5min_kyiv(local).strftime("%H:%M")
    if period == "1d":
        return local.strftime("%H:00")
    if period in ("all", "1y"):
        return local.strftime("%m.%y")
    if period in ("7d", "14d", "30d"):
        return local.strftime("%m.%d")
    return local.strftime("%H:%M")
