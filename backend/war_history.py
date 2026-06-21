"""Full-war analytics: fetch all oblasts from alerts.in.ua and persist monthly aggregates."""

from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from datetime import datetime

import requests

from alerts_service import get_alerts_service
from config import get_settings
from data_loader import transform_alerts
from kyiv_time import WAR_START_KYIV, now_kyiv, to_kyiv, war_start_utc
from regions_data import API_OBLAST_UID_TO_SLUG

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent / "data"
_SNAPSHOT_PATH = _DATA_DIR / "war_snapshot.json"
_AGG_PATH = _DATA_DIR / "war_monthly_agg.json"
_SNAPSHOT_TTL_SECONDS = 3600
_FETCH_GAP_SECONDS = 8.0
_BATCH_SIZE = 4
_MAX_RETRIES = 3

_lock = threading.Lock()
_refresh_running = False


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def _fetch_oblast_history(uid: str, period: str = "month_ago") -> List[Dict[str, Any]]:
    svc = get_alerts_service()
    if not svc._is_configured():
        return []
    url = f"https://api.alerts.in.ua/v1/regions/{uid}/alerts/{period}.json"
    settings = get_settings()
    payload: Any = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = requests.get(
                url,
                headers=svc._auth_headers(),
                timeout=settings.request_timeout_seconds,
            )
            if response.status_code == 429:
                wait = 45 * (attempt + 1)
                logger.warning("Rate limit uid=%s, retry in %ds", uid, wait)
                time.sleep(wait)
                continue
            response.raise_for_status()
            payload = response.json()
            break
        except requests.RequestException as exc:
            logger.warning("Oblast history fetch failed uid=%s: %s", uid, exc)
            return []
    if payload is None:
        return []

    alerts: Any = payload.get("alerts", payload) if isinstance(payload, dict) else payload
    return [item for item in alerts if isinstance(item, dict)] if isinstance(alerts, list) else []


def fetch_all_oblasts_history(period: str = "month_ago") -> List[Dict[str, Any]]:
    """Fetch month_ago history for every oblast (rate-limit safe, ~3 min)."""
    uids = list(API_OBLAST_UID_TO_SLUG.keys())
    all_raw: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()

    for batch_start in range(0, len(uids), _BATCH_SIZE):
        batch = uids[batch_start : batch_start + _BATCH_SIZE]
        for uid in batch:
            for item in _fetch_oblast_history(uid, period):
                rid = str(item.get("id", ""))
                if rid and rid in seen_ids:
                    continue
                if rid:
                    seen_ids.add(rid)
                all_raw.append(item)
            time.sleep(_FETCH_GAP_SECONDS)

    return all_raw


def _month_key_from_record(rec: Dict[str, Any]) -> Optional[str]:
    start = rec.get("start_time") or rec.get("started_at")
    if not start:
        return None
    try:
        from datetime import datetime, timezone

        dt = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return to_kyiv(dt).strftime("%m.%y")
    except (ValueError, TypeError):
        return None


def update_monthly_aggregates(records: List[Dict[str, Any]]) -> None:
    """Persist per-month air/other counts and seen alert ids (survives across fetches)."""
    agg: Dict[str, Any] = _load_json(_AGG_PATH) or {"months": {}, "seen_ids": []}
    months: Dict[str, Dict[str, int]] = agg.setdefault("months", {})
    seen: Set[str] = set(str(x) for x in agg.get("seen_ids", []))

    for rec in records:
        rid = str(rec.get("id") or "")
        if rid and rid in seen:
            continue
        month = _month_key_from_record(rec)
        if not month:
            continue
        bucket = months.setdefault(month, {"air_raid": 0, "other": 0, "total": 0})
        atype = str(rec.get("alert_type") or "")
        if "air" in atype or "raid" in atype:
            bucket["air_raid"] += 1
        else:
            bucket["other"] += 1
        bucket["total"] += 1
        if rid:
            seen.add(rid)

    agg["seen_ids"] = sorted(seen)[-500_000:]
    agg["updated_at"] = time.time()
    _save_json(_AGG_PATH, agg)


def refresh_war_snapshot(*, force: bool = False) -> int:
    """Download all oblast histories and update caches. Returns record count."""
    global _refresh_running
    with _lock:
        if _refresh_running and not force:
            return 0
        _refresh_running = True

    try:
        if not force:
            cached = _load_json(_SNAPSHOT_PATH)
            if isinstance(cached, dict):
                age = time.time() - float(cached.get("fetched_at", 0))
                if age < _SNAPSHOT_TTL_SECONDS and cached.get("records"):
                    return len(cached["records"])

        logger.info("Refreshing full-war snapshot from alerts.in.ua (all oblasts)…")
        raw = fetch_all_oblasts_history("month_ago")
        records = transform_alerts(raw)
        _save_json(
            _SNAPSHOT_PATH,
            {
                "fetched_at": time.time(),
                "source": "alerts.in.ua",
                "oblasts": len(API_OBLAST_UID_TO_SLUG),
                "records": records,
            },
        )
        update_monthly_aggregates(records)

        from alert_store import upsert_alerts

        upsert_alerts(records)
        logger.info("War snapshot updated: %d records", len(records))
        return len(records)
    finally:
        with _lock:
            _refresh_running = False


def get_monthly_chart_since(cutoff_kyiv: datetime) -> List[Dict[str, Any]]:
    """Monthly bar buckets from persisted aggregates, filtered to months on/after cutoff."""
    agg = _load_json(_AGG_PATH) or {}
    months: Dict[str, Dict[str, int]] = agg.get("months", {})
    labels: List[str] = []
    cursor = cutoff_kyiv.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = now_kyiv().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    while cursor <= end:
        labels.append(cursor.strftime("%m.%y"))
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)
    return [
        {
            "date": label,
            "missiles": months.get(label, {}).get("air_raid", 0),
            "drones": months.get(label, {}).get("other", 0),
            "destroyed": 0,
        }
        for label in labels
    ]


def get_war_monthly_chart() -> List[Dict[str, Any]]:
    """Monthly bar buckets for the full-war chart (persisted + current data)."""
    agg = _load_json(_AGG_PATH) or {}
    months: Dict[str, Dict[str, int]] = agg.get("months", {})

    labels: List[str] = []
    cursor = WAR_START_KYIV.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = now_kyiv().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    while cursor <= end:
        labels.append(cursor.strftime("%m.%y"))
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)

    return [
        {
            "date": label,
            "missiles": months.get(label, {}).get("air_raid", 0),
            "drones": months.get(label, {}).get("other", 0),
            "destroyed": 0,
        }
        for label in labels
    ]


def get_war_records() -> List[Dict[str, Any]]:
    """Merged records for period=all: snapshot + full local store since war start."""
    from alert_store import fetch_history

    since = war_start_utc().isoformat()
    local = fetch_history(since_iso=since, limit=None)

    snapshot = _load_json(_SNAPSHOT_PATH)
    snap_records: List[Dict[str, Any]] = []
    if isinstance(snapshot, dict):
        snap_records = snapshot.get("records") or []

    by_id: Dict[str, Dict[str, Any]] = {}
    for rec in local:
        rid = str(rec.get("id") or "")
        if rid:
            by_id[rid] = rec
    for rec in snap_records:
        rid = str(rec.get("id") or "")
        if rid:
            by_id[rid] = rec
        elif rec:
            by_id[f"snap-{len(by_id)}"] = rec

    merged = list(by_id.values())
    if merged:
        update_monthly_aggregates(merged)
    return merged


def snapshot_age_seconds() -> Optional[float]:
    cached = _load_json(_SNAPSHOT_PATH)
    if not isinstance(cached, dict) or not cached.get("fetched_at"):
        return None
    return time.time() - float(cached["fetched_at"])
