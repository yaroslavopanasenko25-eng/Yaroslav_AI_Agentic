"""Server-rendered web UI (Jinja2) — Python presentation tier for GuardianEye."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from mock_data import SAFETY_TIPS
from regions_data import ALL_REGIONS
from ui_i18n import period_labels, t

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

web = APIRouter(tags=["web"])

REGIONS_UI: List[Dict[str, str]] = [
    {"id": slug, "nameUk": name_uk, "nameEn": name_en}
    for _, slug, name_uk, name_en in ALL_REGIONS
]

PERIODS = ["1h", "1d", "7d", "14d", "30d"]


def _lang(request: Request) -> str:
    q = request.query_params.get("lang")
    if q in ("uk", "en"):
        return q
    cookie = request.cookies.get("lang")
    if cookie in ("uk", "en"):
        return cookie
    return "uk"


def _ctx(request: Request, active_tab: str, **extra: Any) -> Dict[str, Any]:
    lang = _lang(request)
    return {
        "request": request,
        "lang": lang,
        "active_tab": active_tab,
        "t": lambda key: t(key, lang),
        "regions": REGIONS_UI,
        "periods": PERIODS,
        "period_labels": period_labels(lang),
        "safety_tips": SAFETY_TIPS,
        **extra,
    }


@web.get("/", response_class=HTMLResponse)
def page_dashboard(request: Request) -> HTMLResponse:
    map_url = "https://alerts.in.ua/en" if _lang(request) == "en" else "https://alerts.in.ua/"
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        _ctx(request, "dashboard", map_url=map_url),
    )


@web.get("/analysis", response_class=HTMLResponse)
def page_analysis(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "analysis.html", _ctx(request, "analysis"))


@web.get("/safety", response_class=HTMLResponse)
def page_safety(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "safety.html", _ctx(request, "safety"))
