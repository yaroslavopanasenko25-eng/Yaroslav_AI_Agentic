"""Local JSON persistence for alert history (works without Supabase)."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import get_settings
from regions_data import UID_TO_SLUG

_STORE_LOCK = threading.Lock()


def _store_path() -> Path:
    settings = get_settings()
    if settings.alert_store_path:
        return Path(settings.alert_store_path)
    return Path(__file__).resolve().parent / "data" / "alerts_history.json"


def _load_raw() -> List[Dict[str, Any]]:
    path = _store_path()
    if not path.exists():
        return []
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_raw(records: List[Dict[str, Any]]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=2)


def upsert_alerts(records: List[Dict[str, Any]]) -> int:
    """Merge records by id into the local store. Returns count of new/updated rows."""
    if not records:
        return 0

    with _STORE_LOCK:
        existing = {str(r["id"]): r for r in _load_raw() if r.get("id") is not None}
        changed = 0
        for rec in records:
            rid = str(rec.get("id", ""))
            if not rid:
                continue
            if existing.get(rid) != rec:
                changed += 1
            existing[rid] = rec
        _save_raw(list(existing.values()))
        return changed


def fetch_history(
    *,
    limit: Optional[int] = 500,
    since_iso: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return stored alert records newest-first. limit=None → no cap."""
    rows = _load_raw()
    if since_iso:
        rows = [r for r in rows if (r.get("start_time") or "") >= since_iso]
    rows.sort(key=lambda r: r.get("start_time") or "", reverse=True)
    if limit is None:
        return rows
    return rows[:limit]
