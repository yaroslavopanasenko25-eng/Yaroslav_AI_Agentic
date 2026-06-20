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
from typing import Any, Dict, List

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ai_service import chat as grok_chat
from ai_service import forecast as grok_forecast
from config import get_settings
from data_loader import fetch_alerts, run_ingestion, transform_alerts
from database import fetch_rows

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
        "grok_configured": bool(cfg.grok_api_key) and "your-grok" not in cfg.grok_api_key,
        "alerts_configured": bool(cfg.alerts_api_key) and "your-alerts" not in cfg.alerts_api_key,
    }


# ── Alarm map (live from alerts.in.ua) ───────────────────────────────────────


@api.get("/regions", tags=["alarms"])
def get_regions() -> Dict[str, Any]:
    """Return current alarm status for every Ukrainian region.

    Falls back to a static mock list when the alerts.in.ua API key is not yet
    configured, so the frontend map always has data to display.
    """
    try:
        raw = fetch_alerts()
        active_ids: set[str] = {
            str(r.get("location_uid") or r.get("region_id", ""))
            for r in raw
        }
        regions = _build_regions(active_ids)
    except RuntimeError as exc:
        logger.warning("alerts.in.ua unavailable, serving mock regions: %s", exc)
        regions = _build_regions(set())

    from datetime import datetime, timezone
    return {"regions": regions, "updatedAt": datetime.now(timezone.utc).isoformat()}


def _build_regions(active_region_ids: set[str]) -> List[Dict[str, str]]:
    """Build the full 26-region list with statuses derived from live active IDs."""
    ALL_REGIONS = [
        ("1",  "vinnytsia",       "Вінницька",         "Vinnytsia"),
        ("2",  "volyn",           "Волинська",          "Volyn"),
        ("3",  "dnipro",          "Дніпропетровська",  "Dnipropetrovsk"),
        ("4",  "donetsk",         "Донецька",           "Donetsk"),
        ("5",  "zhytomyr",        "Житомирська",        "Zhytomyr"),
        ("6",  "zakarpattia",     "Закарпатська",       "Zakarpattia"),
        ("7",  "zaporizhzhia",    "Запорізька",         "Zaporizhzhia"),
        ("8",  "ivano-frankivsk", "Івано-Франківська",  "Ivano-Frankivsk"),
        ("9",  "kyiv-oblast",     "Київська",           "Kyiv Oblast"),
        ("10", "kirovohrad",      "Кіровоградська",    "Kirovohrad"),
        ("11", "luhansk",         "Луганська",          "Luhansk"),
        ("12", "lviv",            "Львівська",          "Lviv"),
        ("13", "mykolaiv",        "Миколаївська",       "Mykolaiv"),
        ("14", "odesa",           "Одеська",            "Odesa"),
        ("15", "poltava",         "Полтавська",         "Poltava"),
        ("16", "rivne",           "Рівненська",         "Rivne"),
        ("17", "sumy",            "Сумська",            "Sumy"),
        ("18", "ternopil",        "Тернопільська",      "Ternopil"),
        ("19", "kharkiv",         "Харківська",         "Kharkiv"),
        ("20", "kherson",         "Херсонська",         "Kherson"),
        ("21", "khmelnytskyi",    "Хмельницька",        "Khmelnytskyi"),
        ("22", "cherkasy",        "Черкаська",          "Cherkasy"),
        ("23", "chernivtsi",      "Чернівецька",        "Chernivtsi"),
        ("24", "chernihiv",       "Чернігівська",       "Chernihiv"),
        ("25", "kyiv-city",       "м. Київ",            "Kyiv City"),
        ("26", "crimea",          "АР Крим",            "AR Crimea"),
    ]
    OCCUPIED = {"luhansk", "donetsk", "crimea"}

    result = []
    for uid, slug, name_uk, name_en in ALL_REGIONS:
        if slug in OCCUPIED:
            status = "occupied"
        elif uid in active_region_ids or slug in active_region_ids:
            status = "active"
        else:
            status = "clear"
        result.append({"id": slug, "nameUk": name_uk, "nameEn": name_en, "status": status})

    return result


# ── Alarm history (Supabase with mock fallback) ───────────────────────────────


@api.get("/alarms/history", tags=["alarms"])
def get_alarm_history(limit: int = 100) -> Dict[str, Any]:
    """Return historical alert records from Supabase.

    Falls back to an empty list when Supabase is not yet configured.
    """
    try:
        rows = fetch_rows("alerts", limit=limit, order_col="start_time", ascending=False)
        return {"history": rows, "count": len(rows), "source": "supabase"}
    except RuntimeError as exc:
        logger.warning("Supabase unavailable, returning empty history: %s", exc)
        return {"history": [], "count": 0, "source": "unavailable"}


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
        reply = grok_chat(body.message, history=history or None)
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


# ── Mount versioned router ────────────────────────────────────────────────────

app.include_router(api)
