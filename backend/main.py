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
from data_loader import run_ingestion
from database import fetch_rows
from history_analytics import build_analysis_payload
from mock_data import SAFETY_TIPS, generate_mock_history

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
    yield
    task.cancel()
    try:
        await task
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


class ChatResponse(BaseModel):
    reply: str


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


@api.get("/alarms/analysis", tags=["alarms"])
def get_alarm_analysis(
    period: str = Query(default="14d", pattern="^(1h|1d|7d|14d|30d|all)$"),
) -> Dict[str, Any]:
    """Return aggregated chart/table data for the Analysis page."""
    rows, source = _load_history(limit=2000)

    if source == "demo":
        return {
            **build_analysis_payload([], period=period),
            "source": "demo",
            "message": "No stored history yet — demo layout shown until data accumulates.",
        }

    payload = build_analysis_payload(rows, period=period)
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
    """Forward a user message to the Grok safety assistant and return the reply."""
    try:
        history = [{"role": m.role, "content": m.content} for m in body.history]
        reply = grok_chat(body.message, history=history or None, lat=body.lat, lng=body.lng)
        return ChatResponse(reply=reply)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


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
