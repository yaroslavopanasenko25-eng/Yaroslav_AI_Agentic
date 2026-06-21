"""FastAPI application — GuardianEye backend.

Routes
------
GET  /health                    Root heartbeat (container probes)
GET  /api/v1/health             Versioned health with dependency status
GET  /api/v1/regions            Live region alarm statuses from alerts.in.ua
GET  /api/v1/alarms/history     Historical alerts (local store / Supabase)
GET  /api/v1/alarms/analysis    Chart/table aggregates for Analysis page
POST /api/v1/ai/chat            Grok-powered safety-assistant reply
POST /api/v1/ai/forecast        Grok threat-forecast from historical data
POST /api/v1/ingest             Trigger manual alert ingestion from alerts.in.ua
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ai_service import chat as grok_chat
from ai_service import forecast as grok_forecast
from alert_store import fetch_history as fetch_local_history
from alerts_poller import alerts_poll_loop
from alerts_service import get_alerts_service
from config import get_settings
from data_loader import fetch_alerts, run_ingestion, transform_alerts
from database import fetch_rows
from history_analytics import build_analysis_payload
from war_history import get_war_monthly_chart, get_war_records, get_monthly_chart_since, refresh_war_snapshot, snapshot_age_seconds
from kyiv_time import period_cutoff_utc, to_kyiv

# ── Logging ───────────────────────────────────────────────────────────────────

settings = get_settings()
logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background alerts.in.ua poller on startup."""
    task = asyncio.create_task(alerts_poll_loop())
    logger.info(
        "Alerts poller started (interval=%ds)",
        get_settings().alerts_poll_interval_seconds,
    )

    async def _war_refresh_loop() -> None:
        while True:
            try:
                if _alerts_api_configured():
                    await asyncio.to_thread(refresh_war_snapshot)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("War snapshot refresh failed: %s", exc)
            await asyncio.sleep(3600)

    war_task = asyncio.create_task(_war_refresh_loop())
    if _alerts_api_configured():
        asyncio.create_task(asyncio.to_thread(refresh_war_snapshot))

    yield
    task.cancel()
    war_task.cancel()
    for t in (task, war_task):
        try:
            await t
        except asyncio.CancelledError:
            pass


# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="GuardianEye API",
    version="1.0.0",
    description="Ukraine air-raid analytics backend — alarms, AI chat, forecasting.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api/v1")

# ── Request / response models ─────────────────────────────────────────────────


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: List[ChatMessage] = Field(default_factory=list)
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lng: Optional[float] = Field(default=None, ge=-180, le=180)
    region_id: Optional[str] = Field(default=None, max_length=64)
    language: Optional[str] = Field(default="uk", pattern="^(uk|en)$")


class ChatResponse(BaseModel):
    reply: str
    dispatch: Optional[Dict[str, Any]] = None


class ForecastRequest(BaseModel):
    max_rows: int = Field(default=200, ge=1, le=500)


# ── Health ────────────────────────────────────────────────────────────────────


@app.get("/health", tags=["root"])
def root_health() -> Dict[str, str]:
    return {"status": "healthy"}


@api.get("/health", tags=["v1"])
def versioned_health() -> Dict[str, Any]:
    """Return service metadata and dependency availability flags."""
    cfg = get_settings()
    svc = get_alerts_service()
    return {
        "status": "ok",
        "service": "guardianeye-backend",
        "version": "1.0.0",
        "supabase_configured": "your-project" not in cfg.supabase_url,
        "grok_configured": bool(cfg.grok_api_key)
        and not cfg.grok_api_key.startswith("your-")
        and cfg.grok_api_key.startswith("xai-"),
        "alerts_configured": bool(cfg.alerts_api_key) and "your-alerts" not in cfg.alerts_api_key,
        "alerts_source": svc.get_source(),
        "active_alerts_count": len(svc.get_alerts()),
    }


# ── Alarm map (cached live data from alerts.in.ua) ────────────────────────────


@api.get("/regions", tags=["alarms"])
def get_regions() -> Dict[str, Any]:
    """Return current alarm status for every Ukrainian region (from server cache)."""
    return get_alerts_service().get_regions_payload()


# ── Alarm history ─────────────────────────────────────────────────────────────


def _load_history(limit: int = 500) -> tuple[List[Dict[str, Any]], str]:
    """Load history from Supabase, local store, or demo fallback."""
    try:
        rows = fetch_rows("alerts", limit=limit, order_col="start_time", ascending=False)
        if rows:
            return rows, "supabase"
    except RuntimeError as exc:
        logger.debug("Supabase history unavailable: %s", exc)

    local = fetch_local_history(limit=limit)
    if local:
        return local, "local"

    return generate_mock_history(), "demo"


@api.get("/alarms/history", tags=["alarms"])
def get_alarm_history(limit: int = 100) -> Dict[str, Any]:
    """Return historical alert records."""
    rows, source = _load_history(limit=limit)
    return {"history": rows, "count": len(rows), "source": source}


def _alerts_api_configured() -> bool:
    cfg = get_settings()
    return bool(cfg.alerts_api_key) and "your-alerts" not in cfg.alerts_api_key


def _load_analysis_records(limit: int = 5000, period: str = "14d") -> tuple[List[Dict[str, Any]], str]:
    """Prefer live alerts.in.ua data; merge with stored history for longer periods."""
    cutoff = period_cutoff_utc(period)
    since_iso = cutoff.isoformat()

    if period == "all":
        if _alerts_api_configured():
            age = snapshot_age_seconds()
            if age is None or age > 3600:
                import threading

                threading.Thread(target=refresh_war_snapshot, kwargs={"force": age is None}, daemon=True).start()
        war_rows = get_war_records()
        local_rows = fetch_local_history(limit=None)
        by_id: Dict[str, Dict[str, Any]] = {}
        for rec in war_rows:
            rid = str(rec.get("id") or "")
            if rid:
                by_id[rid] = rec
        for rec in local_rows:
            rid = str(rec.get("id") or "")
            if rid:
                by_id[rid] = rec
        merged = list(by_id.values())
        if merged:
            hist_source = "live" if war_rows else "local"
            if war_rows and local_rows:
                hist_source = "live"
            return merged, hist_source
        return _load_history(limit=limit)

    live_records: List[Dict[str, Any]] = []
    if _alerts_api_configured():
        try:
            live_records = transform_alerts(fetch_alerts())
        except Exception as exc:
            logger.warning("Live alerts fetch failed: %s", exc)
        if not live_records:
            cached = transform_alerts(get_alerts_service().get_alerts())
            if cached:
                live_records = cached

    if period in ("7d", "14d", "30d", "1y", "1h", "1d"):
        history_rows = fetch_local_history(since_iso=since_iso, limit=None)
        hist_source = "local" if history_rows else "demo"
        if period == "1y" and _alerts_api_configured():
            war_rows = get_war_records()
            by_id: Dict[str, Dict[str, Any]] = {}
            for rec in war_rows:
                start = rec.get("start_time") or rec.get("started_at") or ""
                if start >= since_iso:
                    rid = str(rec.get("id") or "")
                    if rid:
                        by_id[rid] = rec
            for rec in history_rows:
                rid = str(rec.get("id") or "")
                if rid:
                    by_id[rid] = rec
            history_rows = list(by_id.values())
            if history_rows:
                hist_source = "live"
        if period in ("1h", "1d") and not history_rows:
            history_rows, hist_source = _load_history(limit=limit)
    else:
        history_rows, hist_source = _load_history(limit=limit)

    if live_records:
        by_id: Dict[str, Dict[str, Any]] = {}
        for rec in history_rows:
            if rec.get("id"):
                by_id[str(rec["id"])] = rec
        for rec in live_records:
            by_id[str(rec["id"])] = rec
        return list(by_id.values()), "live"

    return history_rows, hist_source


@api.get("/alarms/active", tags=["alarms"])
def get_active_alarms() -> Dict[str, Any]:
    """Return currently active alerts from alerts.in.ua (same source as the dashboard)."""
    if not _alerts_api_configured():
        raise HTTPException(status_code=503, detail="alerts.in.ua API key not configured")
    records = transform_alerts(fetch_alerts())
    active = [r for r in records if r.get("is_active")]
    active.sort(key=lambda r: r.get("start_time") or "", reverse=True)
    from history_analytics import _to_alarm_event

    return {
        "alerts": [_to_alarm_event(r) for r in active],
        "count": len(active),
        "source": "live",
    }


@api.get("/alarms/analysis", tags=["alarms"])
def get_alarm_analysis(
    period: str = Query(default="14d", pattern="^(1h|1d|7d|14d|30d|1y|all)$"),
) -> Dict[str, Any]:
    """Return aggregated chart/table data for the Analysis page."""
    live_records: List[Dict[str, Any]] = []
    if _alerts_api_configured():
        svc = get_alerts_service()
        svc.refresh_active()
        live_records = transform_alerts(svc.get_alerts())
        if not live_records:
            try:
                live_records = transform_alerts(fetch_alerts())
            except Exception as exc:
                logger.warning("Live alerts fallback fetch failed: %s", exc)

    rows, source = _load_analysis_records(limit=5000, period=period)

    if source == "demo" and not _alerts_api_configured():
        return {
            **build_analysis_payload([], period=period),
            "source": "demo",
            "message": "No stored history yet — demo layout shown until data accumulates.",
        }

    war_bar = None
    if period == "all":
        war_bar = get_war_monthly_chart()
    elif period == "1y":
        war_bar = get_monthly_chart_since(to_kyiv(period_cutoff_utc("1y")))

    payload = build_analysis_payload(
        rows,
        period=period,
        live_records=live_records or None,
        war_bar_data=war_bar,
    )
    if period == "all":
        payload["warDataNote"] = (
            "Помісячний графік накопичується з alerts.in.ua; "
            "повна історія з 24.02.2022 оновлюється щогодини."
        )
    elif period == "1y":
        payload["warDataNote"] = (
            "Помісячний графік за рік — дані alerts.in.ua та локальний архів."
        )
    payload["source"] = source
    return payload


# ── Manual ingestion trigger ──────────────────────────────────────────────────


@api.post("/ingest", tags=["alarms"])
def trigger_ingestion() -> Dict[str, Any]:
    """Manually trigger an alerts.in.ua → store/Supabase ingestion run."""
    try:
        count = run_ingestion()
        return {"status": "ok", "records_ingested": count}
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# ── AI chat (Grok) ────────────────────────────────────────────────────────────


@api.post("/ai/chat", response_model=ChatResponse, tags=["ai"])
def ai_chat(body: ChatRequest) -> ChatResponse:
    """RAG-augmented rescue dispatcher chat powered by Grok."""
    try:
        history = [{"role": m.role, "content": m.content} for m in body.history]
        reply, dispatch = grok_chat(
            body.message,
            history=history or None,
            lat=body.lat,
            lng=body.lng,
            region_slug=body.region_id,
            language=body.language or "uk",
        )
        return ChatResponse(reply=reply, dispatch=dispatch)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@api.get("/ai/dispatch", tags=["ai"])
def ai_dispatch_brief(
    region_id: str = Query(default="kyiv-city"),
    lat: Optional[float] = Query(default=None, ge=-90, le=90),
    lng: Optional[float] = Query(default=None, ge=-180, le=180),
    language: str = Query(default="uk", pattern="^(uk|en)$"),
) -> Dict[str, Any]:
    """Return dispatcher priority, risk stats, and shelter hints without calling Grok."""
    return build_dispatch_meta(
        region_slug=region_id,
        lat=lat,
        lng=lng,
        language=language,
    )


# ── AI forecast (Grok) ────────────────────────────────────────────────────────


@api.post("/ai/forecast", tags=["ai"])
def ai_forecast(body: ForecastRequest) -> Dict[str, Any]:
    """Generate a next-day regional threat forecast using Grok + historical data."""
    rows, _ = _load_history(limit=body.max_rows)

    if not rows:
        raise HTTPException(
            status_code=422,
            detail="No historical data available for forecasting. "
                   "Wait for the background poller to accumulate data, or run /api/v1/ingest.",
        )

    try:
        result = grok_forecast(rows, max_rows=body.max_rows)
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# ── Legacy /api routes (frontend compatibility) ─────────────────────────────

legacy = APIRouter(prefix="/api")


@legacy.get("/regions", tags=["legacy"])
def legacy_regions() -> Dict[str, Any]:
    return get_alerts_service().get_regions_payload()


@legacy.get("/alarms/history", tags=["legacy"])
def legacy_history() -> Dict[str, Any]:
    result = get_alarm_history()
    return {"history": result["history"]}


@legacy.get("/alarms/analysis", tags=["legacy"])
def legacy_analysis(period: str = Query(default="14d")) -> Dict[str, Any]:
    return get_alarm_analysis(period=period)


@legacy.get("/safety-tips", tags=["legacy"])
def legacy_safety_tips() -> Dict[str, Any]:
    return SAFETY_TIPS


# ── Mount routers ─────────────────────────────────────────────────────────────

app.include_router(api)
app.include_router(legacy)
