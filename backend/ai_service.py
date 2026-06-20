"""Grok (xAI) integration: chat assistant and threat-forecast functions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

import requests

from agent_context import build_agent_context
from config import get_settings

# System prompt — agent must answer from injected live data, never deflect to external apps
_CHAT_SYSTEM_PROMPT = (
    "You are GuardianEye AI — the built-in safety assistant of this Ukraine air-raid alert app.\n"
    "On every request you receive LIVE APP DATA below. Answer DIRECTLY from that data.\n"
    "Rules:\n"
    "- NEVER say you lack real-time information when live data is provided below.\n"
    "- NEVER redirect users to external apps or websites (Повітряна тривога, air-alarms.in.ua, etc.) "
    "— you ARE the app assistant and the data below IS your source.\n"
    "- When asked about alarms: list the specific regions and their status from the data.\n"
    "- When asked about shelters: give specific addresses, districts, and types from the data.\n"
    "- Be concise, practical, and empathetic. Reply in the same language the user uses.\n"
    "- If data source is demo/mock, mention it briefly but still answer with the listed data.\n"
    "- For emergencies remind to call 112."
)
# System prompt for the analytical forecasting feature
_FORECAST_SYSTEM_PROMPT = (
    "You are a defense analytics forecaster for Ukraine air raid risk. "
    "Use the historical alert rows provided to estimate next-day regional risk probabilities. "
    "Return ONLY strict JSON with keys: date, regional_probabilities, confidence, rationale."
)


def _post_to_grok(messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
    """Send a messages list to the Grok API and return the assistant reply text.

    Raises:
        RuntimeError: When the API key is missing or the request fails.
    """
    settings = get_settings()

    if not settings.grok_api_key or settings.grok_api_key.startswith("your-"):
        raise RuntimeError(
            "Grok API key is not configured. Set XAI_API_KEY or GROK_API_KEY in your .env file."
        )

    headers = {
        "Authorization": f"Bearer {settings.grok_api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": settings.grok_model,
        "messages": messages,
        "temperature": temperature,
    }

    try:
        response = requests.post(
            settings.grok_api_url,
            headers=headers,
            json=payload,
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except requests.HTTPError as exc:
        detail = ""
        if exc.response is not None:
            try:
                detail = exc.response.json().get("error", {}).get("message", "")
            except Exception:
                detail = exc.response.text[:200]
        msg = detail or str(exc)
        raise RuntimeError(f"Grok API error: {msg}") from exc
    except (requests.RequestException, KeyError, IndexError) as exc:
        raise RuntimeError("Grok API request failed.") from exc


# ── Public interface ──────────────────────────────────────────────────────────

def chat(
    user_message: str,
    history: List[Dict[str, str]] | None = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
) -> str:
    """Send a user message to the safety-chat assistant and return the reply.

    Args:
        user_message: The text typed by the user in the AI Agent window.
        history:      Optional list of previous ``{"role": ..., "content": ...}``
                      messages to maintain conversational context.
        lat/lng:      Optional user coordinates for nearest-shelter queries.

    Returns:
        The assistant reply as a plain string.
    """
    context = build_agent_context(user_message, lat=lat, lng=lng)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    system_content = (
        f"{_CHAT_SYSTEM_PROMPT}\n\n"
        f"=== LIVE APP DATA ({timestamp}) ===\n"
        f"{context}\n"
        f"=== END LIVE APP DATA ==="
    )

    messages: List[Dict[str, str]] = [{"role": "system", "content": system_content}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return _post_to_grok(messages, temperature=0.3)

def forecast(historical_rows: Iterable[Dict[str, Any]], max_rows: int = 200) -> Dict[str, Any]:
    """Request a threat forecast from Grok using historical alert data.

    Args:
        historical_rows: Iterable of alert dicts (from Supabase or the mock data).
        max_rows:        Maximum number of rows to include in the prompt context.

    Returns:
        Parsed JSON dict with forecast data, or a raw string on parse failure.
    """
    if max_rows <= 0:
        raise ValueError("`max_rows` must be greater than zero.")

    lines = [
        json.dumps(row, ensure_ascii=False, default=str)
        for i, row in enumerate(historical_rows)
        if i < max_rows
    ]
    context = "\n".join(lines) if lines else "No historical rows available."

    prompt = (
        f"{_FORECAST_SYSTEM_PROMPT}\n\n"
        f"Historical rows:\n{context}"
    )
    messages = [{"role": "user", "content": prompt}]
    raw_reply = _post_to_grok(messages, temperature=0.2)

    try:
        return json.loads(raw_reply)
    except json.JSONDecodeError:
        return {"raw": raw_reply}
