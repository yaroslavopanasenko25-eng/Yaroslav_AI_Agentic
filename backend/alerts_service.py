"""Cached alerts.in.ua client — single upstream poller, rate-limit safe.

Docs: https://devs.alerts.in.ua/
- Auth: Authorization: Bearer <token>
- Rate limit: 8–10 soft / 12 hard requests per minute per IP
- Cache: If-Modified-Since → 304 when unchanged
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from email.utils import formatdate, parsedate_to_datetime
from typing import Any, Dict, List, Optional, Tuple

import requests

from config import get_settings
from regions_data import (
    build_regions_from_slugs,
    parse_iot_oblast_levels,
    parse_iot_oblast_status,
    slug_from_alert,
)

logger = logging.getLogger(__name__)

# Minimum gap between upstream calls (seconds). 30s → 2 req/min (well under quota).
_MIN_ACTIVE_INTERVAL = 6.0
_MIN_HISTORY_INTERVAL = 30.0


class AlertsService:
    """Thread-safe cache + upstream fetcher for alerts.in.ua."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._alerts: List[Dict[str, Any]] = []
        self._last_modified: Optional[str] = None
        self._last_fetch_at: float = 0.0
        self._last_history_fetch_at: float = 0.0
        self._iot_status: str = ""
        self._last_iot_fetch_at: float = 0.0
        self._source: str = "demo"
        self._last_error: Optional[str] = None
        self._meta: Dict[str, Any] = {}

    # ── Public read API (no upstream calls) ───────────────────────────────────

    def get_alerts(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._alerts)

    def get_source(self) -> str:
        with self._lock:
            return self._source

    def get_last_error(self) -> Optional[str]:
        with self._lock:
            return self._last_error

    def get_regions_payload(self) -> Dict[str, Any]:
        with self._lock:
            iot_status = self._iot_status
            source = self._source
            meta = dict(self._meta)

        levels: dict[str, str] = {}
        if source == "live" and iot_status:
            active_slugs, warning_slugs = parse_iot_oblast_status(iot_status)
            levels = parse_iot_oblast_levels(iot_status)
            regions = build_regions_from_slugs(active_slugs, warning_slugs)
        elif source == "live":
            regions = build_regions_from_slugs(set(), set())
        else:
            regions = build_regions_from_slugs(use_mock=True)

        if levels:
            for region in regions:
                region["level"] = levels.get(region["id"], "N")

        threats = _build_threat_markers(self.get_alerts()) if source == "live" else []

        updated = meta.get("last_updated_at") or datetime.now(timezone.utc).isoformat()
        alarm_count = sum(
            1 for r in regions if r.get("status") in ("active", "warning")
        )
        return {
            "regions": regions,
            "threats": threats,
            "updatedAt": updated,
            "source": source,
            "iotStatus": iot_status if source == "live" else None,
            "alarmCount": alarm_count,
        }

    # ── Upstream fetch ────────────────────────────────────────────────────────

    def _is_configured(self) -> bool:
        return get_settings().is_alerts_configured()

    def _auth_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {"Authorization": f"Bearer {get_settings().alerts_api_key}"}
        if extra:
            headers.update(extra)
        return headers

    def refresh_active(self, *, force: bool = False) -> bool:
        """Fetch /v1/alerts/active.json. Returns True when data changed."""
        if not self._is_configured():
            with self._lock:
                self._source = "demo"
                self._last_error = "ALERTS_API_KEY not configured"
            return False

        now = time.monotonic()
        with self._lock:
            if not force and now - self._last_fetch_at < _MIN_ACTIVE_INTERVAL:
                return False
            last_modified = self._last_modified

        headers = self._auth_headers()
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        settings = get_settings()
        try:
            response = requests.get(
                settings.alerts_api_url,
                headers=headers,
                timeout=settings.request_timeout_seconds,
            )
        except requests.RequestException as exc:
            with self._lock:
                self._last_error = str(exc)
            logger.warning("alerts.in.ua request failed: %s", exc)
            return False

        if response.status_code == 304:
            with self._lock:
                self._last_fetch_at = now
                self._source = "live"
                self._last_error = None
            return False

        if response.status_code == 429:
            with self._lock:
                self._last_error = "Rate limit exceeded (429)"
            logger.warning("alerts.in.ua rate limit hit")
            return False

        try:
            response.raise_for_status()
            payload: Any = response.json()
        except (requests.HTTPError, ValueError) as exc:
            with self._lock:
                self._last_error = str(exc)
            logger.warning("alerts.in.ua bad response: %s", exc)
            return False

        alerts: Any = payload.get("alerts", payload) if isinstance(payload, dict) else payload
        if not isinstance(alerts, list):
            with self._lock:
                self._last_error = "Unexpected response format"
            return False

        meta = payload.get("meta", {}) if isinstance(payload, dict) else {}
        resp_lm = response.headers.get("Last-Modified")
        if not resp_lm and meta.get("last_updated_at"):
            try:
                dt = datetime.fromisoformat(str(meta["last_updated_at"]).replace("Z", "+00:00"))
                resp_lm = formatdate(dt.timestamp(), usegmt=True)
            except (ValueError, TypeError):
                pass

        records = [item for item in alerts if isinstance(item, dict)]
        with self._lock:
            self._alerts = records
            self._last_fetch_at = now
            self._source = "live"
            self._last_error = None
            self._meta = meta if isinstance(meta, dict) else {}
            if resp_lm:
                self._last_modified = resp_lm

        return True

    def refresh_oblast_iot(self, *, force: bool = False) -> bool:
        """Fetch /v1/iot/active_air_raid_alerts_by_oblast.json for map statuses."""
        if not self._is_configured():
            return False

        now = time.monotonic()
        with self._lock:
            if not force and now - self._last_iot_fetch_at < _MIN_ACTIVE_INTERVAL:
                return False

        settings = get_settings()
        url = "https://api.alerts.in.ua/v1/iot/active_air_raid_alerts_by_oblast.json"
        try:
            response = requests.get(
                url,
                headers=self._auth_headers(),
                timeout=settings.request_timeout_seconds,
            )
            response.raise_for_status()
            payload: Any = response.json()
        except requests.RequestException as exc:
            logger.warning("alerts.in.ua IoT request failed: %s", exc)
            return False

        status_line = payload if isinstance(payload, str) else str(payload)
        with self._lock:
            self._iot_status = status_line
            self._last_iot_fetch_at = now
            self._source = "live"
            self._last_error = None
        return True

    def fetch_region_history(self, region_uid: str, period: str = "month_ago") -> List[Dict[str, Any]]:
        """Fetch /v1/regions/{uid}/alerts/{period}.json (2 req/min limit)."""
        if not self._is_configured():
            return []

        now = time.monotonic()
        with self._lock:
            if now - self._last_history_fetch_at < _MIN_HISTORY_INTERVAL:
                return []
            self._last_history_fetch_at = now

        url = f"https://api.alerts.in.ua/v1/regions/{region_uid}/alerts/{period}.json"
        settings = get_settings()
        try:
            response = requests.get(
                url,
                headers=self._auth_headers(),
                timeout=settings.request_timeout_seconds,
            )
            if response.status_code == 429:
                logger.warning("alerts.in.ua history rate limit for uid=%s", region_uid)
                return []
            response.raise_for_status()
            payload: Any = response.json()
        except requests.RequestException as exc:
            logger.warning("History fetch failed uid=%s: %s", region_uid, exc)
            return []

        alerts: Any = payload.get("alerts", payload) if isinstance(payload, dict) else payload
        if not isinstance(alerts, list):
            return []
        return [item for item in alerts if isinstance(item, dict)]


def _build_threat_markers(alerts: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Non-air-raid alerts → map threat icons (artillery, urban fights, etc.)."""
    markers: List[Dict[str, str]] = []
    seen: set[str] = set()
    for item in alerts:
        alert_type = str(item.get("alert_type") or "")
        if alert_type in ("air_raid", ""):
            continue
        slug = slug_from_alert(item)
        if not slug or slug in seen:
            continue
        seen.add(slug)
        markers.append({"slug": slug, "type": alert_type})
    return markers


# Module singleton — all routes and background tasks share one cache.
_service = AlertsService()


def get_alerts_service() -> AlertsService:
    return _service


def fetch_alerts() -> List[Dict[str, Any]]:
    """Compatibility wrapper used by data_loader / agent_context."""
    svc = get_alerts_service()
    svc.refresh_active()
    return svc.get_alerts()
