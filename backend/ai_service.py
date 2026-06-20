"""Grok (xAI) integration: chat assistant and threat-forecast functions."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List

import requests

from config import get_settings

# System prompt for the safety-chat assistant (used by the frontend AI Agent)
_CHAT_SYSTEM_PROMPT = (
    "You are a safety assistant for Ukraine air raid alerts. "
    "Answer questions about air alarms, shelters, safety rules, and emergency procedures. "
    "Keep answers concise and practical. "
    "When relevant, remind users to call 112 for emergencies. "
    "Reply in the same language the user used."
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

    if not settings.grok_api_key or "your-grok" in settings.grok_api_key:
        raise RuntimeError(
            "Grok API key is not configured. Set GROK_API_KEY in your .env file."
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
    except (requests.RequestException, KeyError, IndexError) as exc:
        raise RuntimeError("Grok API request failed.") from exc


# ── Public interface ──────────────────────────────────────────────────────────

def chat(user_message: str, history: List[Dict[str, str]] | None = None) -> str:
    """Send a user message to the safety-chat assistant and return the reply.

    Args:
        user_message: The text typed by the user in the AI Agent window.
        history:      Optional list of previous ``{"role": ..., "content": ...}``
                      messages to maintain conversational context.

    Returns:
        The assistant reply as a plain string.
    """
    messages: List[Dict[str, str]] = [{"role": "system", "content": _CHAT_SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return _post_to_grok(messages, temperature=0.4)


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
