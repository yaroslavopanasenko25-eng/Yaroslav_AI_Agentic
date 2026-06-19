"""Grok API integration template for GuardianEye predictive threat forecasting."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List

import requests

GROK_API_URL: str = os.getenv("GROK_API_URL", "https://api.x.ai/v1/chat/completions")
GROK_API_KEY: str = os.getenv("GROK_API_KEY", "")
GROK_MODEL: str = os.getenv("GROK_MODEL", "grok-3-mini")
REQUEST_TIMEOUT_SECONDS: int = 30


def format_historical_context(rows: Iterable[Dict[str, Any]], max_rows: int = 200) -> str:
    """Format historical alert/interception records into compact JSONL context."""
    if max_rows <= 0:
        raise ValueError("`max_rows` must be greater than zero.")

    formatted_lines: List[str] = []
    for index, row in enumerate(rows):
        if index >= max_rows:
            break
        formatted_lines.append(json.dumps(row, ensure_ascii=False, default=str))

    if not formatted_lines:
        return "No historical rows available."

    return "\n".join(formatted_lines)


def build_forecast_prompt(context: str) -> str:
    """Build structured forecasting prompt for next-day regional risk estimation."""
    return (
        "You are a defense analytics forecaster for Ukraine air raid risk. "
        "Use the historical rows to estimate next-day regional risk probabilities. "
        "Return strict JSON with keys: date, regional_probabilities, confidence, rationale.\n\n"
        f"Historical rows:\n{context}"
    )


def request_grok_forecast(historical_rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Request a forecast from Grok API using historical defense analytics context."""
    if not GROK_API_KEY:
        raise RuntimeError("GROK_API_KEY must be set in environment variables.")

    context: str = format_historical_context(historical_rows)
    prompt: str = build_forecast_prompt(context)

    headers: Dict[str, str] = {
        "Authorization": "Bearer " + GROK_API_KEY,
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": GROK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }

    try:
        response: requests.Response = requests.post(
            GROK_API_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise RuntimeError("Grok API forecasting request failed.") from exc
