"""Build live app-data context injected into every Grok chat request."""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import get_settings
from data_loader import fetch_alerts
from database import fetch_rows
from regions_data import build_regions

_SHELTERS_PATH = (
    Path(__file__).resolve().parent.parent
    / "alarm-app" / "frontend" / "public" / "shelters.json"
)

_KYIV_DISTRICTS = [
    "Голосіївський", "Дарницький", "Деснянський", "Дніпровський",
    "Оболонський", "Печерський", "Подільський", "Святошинський",
    "Солом'янський", "Шевченківський",
]

_SHELTER_KEYWORDS = re.compile(
    r"укрит|укрыт|схов|убежищ|shelter|укритт|метро|підвал|подвал|бомбосхов",
    re.IGNORECASE,
)
_ALARM_KEYWORDS = re.compile(
    r"тривог|тревог|alarm|alert|ракет|дрон|шахед|загроз|угроз|де\s+тривог",
    re.IGNORECASE,
)


@lru_cache(maxsize=1)
def _load_shelters() -> List[Dict[str, Any]]:
    if not _SHELTERS_PATH.exists():
        return []
    with _SHELTERS_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlng / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def _get_live_regions() -> tuple[List[Dict[str, str]], str]:
    """Return (regions, source_label)."""
    settings = get_settings()

    if settings.alerts_api_key and not settings.alerts_api_key.startswith("your-"):
        try:
            raw = fetch_alerts()
            active_ids = {
                str(r.get("location_uid") or r.get("region_id", ""))
                for r in raw
            }
            return build_regions(active_ids), "alerts.in.ua (live)"
        except RuntimeError:
            pass

    return build_regions(use_mock=True), "app dashboard (demo data)"


def _format_alarm_section() -> str:
    regions, source = _get_live_regions()
    active = [r for r in regions if r["status"] == "active"]
    warning = [r for r in regions if r["status"] == "warning"]
    occupied = [r for r in regions if r["status"] == "occupied"]
    clear_count = sum(1 for r in regions if r["status"] == "clear")

    lines = [
        f"## Поточні повітряні тривоги (джерело: {source})",
        f"Оновлено: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
    ]

    if active:
        lines.append(f"🔴 АКТИВНА ТРИВОГА ({len(active)}): " + ", ".join(r["nameUk"] for r in active))
    else:
        lines.append("🔴 Активних тривог зараз немає.")

    if warning:
        lines.append(f"🟠 Попередження ({len(warning)}): " + ", ".join(r["nameUk"] for r in warning))

    if occupied:
        lines.append(f"⚫ Окуповані території ({len(occupied)}): " + ", ".join(r["nameUk"] for r in occupied))

    lines.append(f"🟢 Без тривоги: {clear_count} областей")

    # Raw alert details when live API available
    settings = get_settings()
    if settings.alerts_api_key and not settings.alerts_api_key.startswith("your-"):
        try:
            raw = fetch_alerts()
            if raw:
                lines.append("\nДеталі активних тривог:")
                for item in raw[:20]:
                    title = item.get("location_title") or item.get("region", "?")
                    atype = item.get("alert_type") or item.get("threat_type") or "тривога"
                    started = item.get("started_at") or item.get("start_time") or "?"
                    lines.append(f"  • {title} — {atype}, початок: {started}")
        except RuntimeError:
            pass

    return "\n".join(lines)


def _search_shelters(
    query: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    limit: int = 8,
) -> List[Dict[str, Any]]:
    shelters = _load_shelters()
    if not shelters:
        return []

    q_lower = query.lower()

    # Match Kyiv district mentioned in query
    district_filter: Optional[str] = None
    for d in _KYIV_DISTRICTS:
        if d.lower() in q_lower:
            district_filter = d
            break

    pool = shelters
    if district_filter:
        pool = [s for s in pool if s.get("city", "").lower() == district_filter.lower()]

    # Address / street keyword filter
    words = [w for w in re.split(r"\s+", q_lower) if len(w) > 3 and w not in ("де", "най", "ближ", "укрит", "тривог")]
    if words and not district_filter:
        filtered = [
            s for s in pool
            if any(w in s.get("nameUk", "").lower() or w in s.get("city", "").lower() for w in words)
        ]
        if filtered:
            pool = filtered

    if lat is not None and lng is not None:
        pool = sorted(pool, key=lambda s: _haversine_km(lat, lng, s["lat"], s["lng"]))

    return pool[:limit]


def _format_shelter_section(query: str, lat: Optional[float], lng: Optional[float]) -> str:
    shelters = _load_shelters()
    total = len(shelters)

    lines = [
        f"## Карта укриттів Києва ({total} об'єктів у базі додатку)",
        f"Райони: {', '.join(_KYIV_DISTRICTS)}",
    ]

    if lat is not None and lng is not None:
        lines.append(f"Координати користувача: {lat:.5f}, {lng:.5f}")

    matches = _search_shelters(query, lat=lat, lng=lng)
    if matches:
        label = "Найближчі укриття" if lat else "Релевантні укриття"
        lines.append(f"\n{label}:")
        for s in matches:
            kind = s.get("kind") or s.get("type", "")
            dist = ""
            if lat is not None and lng is not None:
                km = _haversine_km(lat, lng, s["lat"], s["lng"])
                dist = f" (~{km:.1f} км)"
            lines.append(
                f"  • {s['nameUk']}, {s.get('city', '')} — {kind}{dist} "
                f"[{s['lat']}, {s['lng']}]"
            )
    elif _SHELTER_KEYWORDS.search(query):
        # Generic shelter query — show a sample from each district
        lines.append("\nПриклади укриттів по районах:")
        for district in _KYIV_DISTRICTS[:5]:
            sample = next((s for s in shelters if s.get("city") == district), None)
            if sample:
                lines.append(f"  • {district}: {sample['nameUk']} ({sample.get('kind', '')})")

    return "\n".join(lines)


def _format_history_section() -> str:
    try:
        rows = fetch_rows("alerts", limit=5, order_col="start_time", ascending=False)
    except RuntimeError:
        rows = []

    if not rows:
        return "## Історія тривог\nНемає збережених записів (Supabase не налаштовано)."

    lines = ["## Останні тривоги (історія)"]
    for row in rows:
        region = row.get("region") or row.get("region_id", "?")
        start = row.get("start_time", "?")
        duration = row.get("duration_minutes")
        dur = f", {duration} хв" if duration else ""
        lines.append(f"  • {region} — {start}{dur}")
    return "\n".join(lines)


def _format_safety_section() -> str:
    return """## Правила безпеки (з додатку)
- Під час тривоги: негайно йдіть до найближчого укриття, подалі від вікон.
- Тривожна валіза: документи, вода (3 л/добу), ліки, ліхтарик, заряджений телефон.
- Після відбою: зачекайте 15–20 хвилин перед виходом.
- Екстрені служби: 112 (єдиний), 101 (пожежна), 103 (швидка)."""


def build_agent_context(
    user_message: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
) -> str:
    """Assemble live data context for the Grok system prompt."""
    sections: List[str] = []

    if _ALARM_KEYWORDS.search(user_message) or True:
        sections.append(_format_alarm_section())

    if _SHELTER_KEYWORDS.search(user_message) or lat is not None:
        sections.append(_format_shelter_section(user_message, lat, lng))
    elif _ALARM_KEYWORDS.search(user_message):
        # Always include shelter summary when discussing alarms
        sections.append(_format_shelter_section("укриття", lat, lng))

    sections.append(_format_safety_section())
    sections.append(_format_history_section())

    return "\n\n".join(sections)
