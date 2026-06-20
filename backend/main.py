"""FastAPI application — GuardianEye backend.

Routes
------
GET  /health                    Root heartbeat (container probes)
GET  /api/v1/health             Versioned health with dependency status
GET  /api/v1/regions            Live region alarm statuses from alerts.in.ua
GET  /api/v1/alarms/history     Historical alerts from Supabase (with mock fallback)
POST /api/v1/ai/chat            Grok-powered safety-assistant reply
POST /api/v1/ai/forecast        Grok threat-forecast from historical data
POST /api/v1/ingest             Trigger manual alert ingestion from alerts.in.ua
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ai_service import chat as grok_chat
from ai_service import forecast as grok_forecast
from config import get_settings
from data_loader import fetch_alerts, run_ingestion, transform_alerts
from database import fetch_rows
from mock_data import SAFETY_TIPS, generate_mock_history
from regions_data import build_regions

# ── Logging ───────────────────────────────────────────────────────────────────

settings = get_settings()
logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger(__name__)

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="GuardianEye API",
    version="1.0.0",
    description="Ukraine air-raid analytics backend — alarms, AI chat, forecasting.",
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
    return {
        "status": "ok",
        "service": "guardianeye-backend",
        "version": "1.0.0",
        "supabase_configured": "your-project" not in cfg.supabase_url,
        "grok_configured": bool(cfg.grok_api_key)
        and not cfg.grok_api_key.startswith("your-")
        and cfg.grok_api_key.startswith("xai-"),
        "alerts_configured": bool(cfg.alerts_api_key) and "your-alerts" not in cfg.alerts_api_key,
    }


# ── Shared helpers ────────────────────────────────────────────────────────────


def _regions_payload() -> Dict[str, Any]:
    """Build the region list response (live API or demo fallback)."""
    try:
        raw = fetch_alerts()
        active_ids: set[str] = {
            str(r.get("location_uid") or r.get("region_id", ""))
            for r in raw
        }
        regions = build_regions(active_ids)
        source = "live"
    except RuntimeError as exc:
        logger.warning("alerts.in.ua unavailable, serving demo regions: %s", exc)
        regions = build_regions(use_mock=True)
        source = "demo"

    from datetime import datetime, timezone
    return {
        "regions": regions,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "source": source,
    }


# ── Alarm map (live from alerts.in.ua) ───────────────────────────────────────


@api.get("/regions", tags=["alarms"])
def get_regions() -> Dict[str, Any]:
    """Return current alarm status for every Ukrainian region."""
    payload = _regions_payload()
    return {"regions": payload["regions"], "updatedAt": payload["updatedAt"]}


# ── Alarm history (Supabase with mock fallback) ───────────────────────────────


@api.get("/alarms/history", tags=["alarms"])
def get_alarm_history(limit: int = 100) -> Dict[str, Any]:
    """Return historical alert records from Supabase, or demo data as fallback."""
    try:
        rows = fetch_rows("alerts", limit=limit, order_col="start_time", ascending=False)
        if rows:
            return {"history": rows, "count": len(rows), "source": "supabase"}
    except RuntimeError as exc:
        logger.warning("Supabase unavailable, serving demo history: %s", exc)

    demo = generate_mock_history()
    return {"history": demo, "count": len(demo), "source": "demo"}


# ── Manual ingestion trigger ──────────────────────────────────────────────────


@api.post("/ingest", tags=["alarms"])
def trigger_ingestion() -> Dict[str, Any]:
    """Manually trigger an alerts.in.ua → Supabase ingestion run."""
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
    """Generate a next-day regional threat forecast using Grok + Supabase data."""
    try:
        rows = fetch_rows("alerts", limit=body.max_rows, order_col="start_time", ascending=False)
    except RuntimeError:
        rows = []

    if not rows:
        raise HTTPException(
            status_code=422,
            detail="No historical data available for forecasting. "
                   "Configure Supabase and run /api/v1/ingest first.",
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
    payload = _regions_payload()
    return {"regions": payload["regions"], "updatedAt": payload["updatedAt"]}


@legacy.get("/alarms/history", tags=["legacy"])
def legacy_history() -> Dict[str, Any]:
    result = get_alarm_history()
    return {"history": result["history"]}


@legacy.get("/safety-tips", tags=["legacy"])
def legacy_safety_tips() -> Dict[str, Any]:
    return SAFETY_TIPS


# ── Mount routers ─────────────────────────────────────────────────────────────

app.include_router(api)
app.include_router(legacy)
