"""Grok (xAI) integration: RAG-augmented chat, forecasting, and dispatcher assistant."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional

import requests

from agent_context import build_agent_context, build_dispatch_meta
from config import get_settings
from risk_predictor import regional_ranking

_CHAT_SYSTEM_PROMPT = (
    "You are GuardianEye AI — the built-in rescue dispatcher and safety assistant for Ukraine.\n"
    "You receive LIVE DATA + RAG protocols + statistical risk + dispatcher assessment below.\n\n"
    "Your role:\n"
    "1. DISPATCHER — give clear priority (critical/high/watch/normal) and numbered action steps.\n"
    "2. PREDICTOR — explain alarm probability from statistics; never guarantee; always defer to official alarms.\n"
    "3. RESCUE GUIDE — shelters, emergency numbers (112/101/103), safety rules.\n\n"
    "Rules:\n"
    "- Answer DIRECTLY from provided data. Never say you lack real-time info when data is below.\n"
    "- Never redirect to external apps or websites.\n"
    "- During ACTIVE alarm in user's oblast: urgent shelter instructions first.\n"
    "- Include nearest shelter names/distances when coordinates are provided.\n"
    "- Reply in the same language the user used.\n"
    "- Be concise, calm, actionable — like a professional emergency dispatcher."
)

_FORECAST_SYSTEM_PROMPT = (
    "You are a defense analytics forecaster for Ukraine air raid risk. "
    "Use the historical rows to estimate next-day regional risk probabilities. "
    "Return strict JSON with keys: date, regional_probabilities, confidence, rationale."
)


def _grok_messages(
    system: str,
    user_content: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_content})
    return messages


def _call_grok(messages: List[Dict[str, str]], *, temperature: float = 0.3) -> str:
    settings = get_settings()
    if not settings.is_grok_configured():
        raise RuntimeError(
            "GROK_API_KEY is not configured. "
            "Copy backend/.env.example to backend/.env and add your xAI key, "
            "or use demo endpoints that work without Grok."
        )

    payload = {
        "model": settings.grok_model,
        "messages": messages,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {settings.grok_api_key}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(
            settings.grok_api_url,
            headers=headers,
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
        data = response.json()
        return str(data["choices"][0]["message"]["content"])
    except (requests.RequestException, KeyError, IndexError) as exc:
        raise RuntimeError("Grok API request failed.") from exc


def _demo_chat_reply(meta: Dict[str, Any], *, language: str) -> str:
    """Rule-based dispatcher reply when Grok API key is not set."""
    is_uk = language == "uk"
    header = meta.get("priority_label") or meta.get("priority") or "GuardianEye"
    region = meta.get("region_name") or "?"
    status = meta.get("status_label") or meta.get("status") or "?"
    lines = [
        f"**{header}** — {region} ({status})",
        "",
    ]
    for i, step in enumerate(meta.get("steps") or [], 1):
        lines.append(f"{i}. {step}")
    shelters = meta.get("nearest_shelters") or []
    if shelters:
        label = "Найближчі укриття" if is_uk else "Nearest shelters"
        lines.extend(["", f"{label}: " + "; ".join(shelters)])
    risk = meta.get("risk") or {}
    prob = risk.get("next_6h_probability")
    if prob is not None:
        label = "Ймовірність тривоги (6 год, статистика)" if is_uk else "Alarm probability (6h, stats)"
        lines.extend(["", f"{label}: {prob}%"])
    lines.extend([
        "",
        "112 · 101 · 103",
        "",
        (
            "ℹ️ Демо-режим без Grok AI. Додайте GROK_API_KEY у backend/.env для повних відповідей."
            if is_uk
            else "ℹ️ Demo mode without Grok AI. Add GROK_API_KEY to backend/.env for full replies."
        ),
    ])
    return "\n".join(lines)


def chat(
    message: str,
    *,
    history: Optional[List[Dict[str, str]]] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    region_slug: Optional[str] = None,
    language: str = "uk",
) -> tuple[str, Dict[str, Any]]:
    """RAG-augmented safety/dispatcher chat. Returns (reply, dispatch_metadata)."""
    context = build_agent_context(
        message,
        lat=lat,
        lng=lng,
        region_slug=region_slug,
        language=language,
    )
    meta = build_dispatch_meta(
        region_slug=region_slug,
        lat=lat,
        lng=lng,
        language=language,
    )
    settings = get_settings()
    if not settings.is_grok_configured():
        return _demo_chat_reply(meta, language=language), {**meta, "demo_mode": True}
    system = f"{_CHAT_SYSTEM_PROMPT}\n\n--- CONTEXT (LIVE + RAG + DISPATCHER) ---\n{context}"
    reply = _call_grok(_grok_messages(system, message, history=history))
    return reply, meta


def _format_historical_context(rows: Iterable[Dict[str, Any]], max_rows: int = 200) -> str:
    lines: List[str] = []
    for index, row in enumerate(rows):
        if index >= max_rows:
            break
        lines.append(json.dumps(row, ensure_ascii=False, default=str))
    return "\n".join(lines) if lines else "No historical rows available."


def forecast(rows: Iterable[Dict[str, Any]], *, max_rows: int = 200) -> Dict[str, Any]:
    """Generate a next-day regional threat forecast from historical alert rows."""
    settings = get_settings()
    if not settings.is_grok_configured():
        from datetime import timedelta

        from kyiv_time import now_kyiv

        ranking = regional_ranking(language="uk", top_n=10)
        probs = {
            item["region_slug"]: round(min(95, max(5, item.get("count_30d", 0) * 2)), 1)
            for item in ranking
        }
        tomorrow = (now_kyiv() + timedelta(days=1)).strftime("%Y-%m-%d")
        return {
            "date": tomorrow,
            "regional_probabilities": probs or {"kyiv-city": 15.0},
            "confidence": "low",
            "rationale": (
                "Demo forecast from 30-day statistics. "
                "Set GROK_API_KEY in backend/.env for AI-generated reasoning."
            ),
            "demo_mode": True,
        }

    context = _format_historical_context(rows, max_rows=max_rows)
    prompt = f"{_FORECAST_SYSTEM_PROMPT}\n\nHistorical rows:\n{context}"
    raw = _call_grok([{"role": "user", "content": prompt}], temperature=0.2)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw, "parse_error": True}
