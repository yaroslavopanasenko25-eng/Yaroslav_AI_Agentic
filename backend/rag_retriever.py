"""Lightweight RAG retrieval over static knowledge chunks and alert statistics."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_KNOWLEDGE_PATH = Path(__file__).resolve().parent / "data" / "rag_knowledge.json"

_STOPWORDS = {
    "the", "and", "for", "you", "your", "what", "how", "when", "where", "that", "this",
    "де", "що", "як", "коли", "чому", "або", "але", "при", "для", "мені", "мене", "мій",
}


@dataclass
class RagChunk:
    id: str
    category: str
    tags: List[str]
    content_uk: str
    content_en: str
    score: float = 0.0

    def text(self, language: str = "uk") -> str:
        return self.content_uk if language == "uk" else self.content_en


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[\w\u0400-\u04FF]+", text.lower())
    return [t for t in tokens if len(t) > 2 and t not in _STOPWORDS]


@lru_cache(maxsize=1)
def _load_chunks() -> List[RagChunk]:
    if not _KNOWLEDGE_PATH.exists():
        return []
    with _KNOWLEDGE_PATH.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    chunks: List[RagChunk] = []
    for item in payload.get("chunks", []):
        chunks.append(
            RagChunk(
                id=str(item.get("id", "")),
                category=str(item.get("category", "general")),
                tags=[str(t).lower() for t in item.get("tags", [])],
                content_uk=str(item.get("content_uk", "")),
                content_en=str(item.get("content_en", "")),
            )
        )
    return chunks


def _category_boost(category: str, query: str) -> float:
    q = query.lower()
    if category == "dispatcher" and re.search(r"диспетч|dispatch|що роб|what to do|протокол", q):
        return 2.5
    if category == "prediction" and re.search(r"прогноз|forecast|коли|when|ймовір|predict", q):
        return 2.5
    if category == "emergency" and re.search(r"112|101|103|екстр|emergency|поран|fire|пожеж", q):
        return 2.5
    if category == "safety" and re.search(r"безпек|safety|укрит|shelter|валіз|prepare", q):
        return 1.5
    return 0.0


def _score_chunk(chunk: RagChunk, query_tokens: Sequence[str], query: str) -> float:
    corpus = " ".join([chunk.content_uk, chunk.content_en, " ".join(chunk.tags)]).lower()
    corpus_tokens = set(_tokenize(corpus))
    if not query_tokens:
        return 0.0

    overlap = sum(1 for t in query_tokens if t in corpus_tokens)
    tag_hits = sum(1 for t in query_tokens if any(t in tag for tag in chunk.tags))
    score = overlap + tag_hits * 1.5 + _category_boost(chunk.category, query)

    # Mild IDF-style boost for rare tag matches
    for t in query_tokens:
        if t in chunk.tags:
            score += 2.0
    return score


def retrieve(
    query: str,
    *,
    language: str = "uk",
    top_k: int = 5,
    min_score: float = 1.0,
) -> List[RagChunk]:
    """Return top-k knowledge chunks ranked by keyword/tag relevance."""
    query_tokens = _tokenize(query)
    ranked: List[RagChunk] = []
    for chunk in _load_chunks():
        score = _score_chunk(chunk, query_tokens, query)
        if score >= min_score:
            ranked.append(RagChunk(
                id=chunk.id,
                category=chunk.category,
                tags=chunk.tags,
                content_uk=chunk.content_uk,
                content_en=chunk.content_en,
                score=score,
            ))
    ranked.sort(key=lambda c: c.score, reverse=True)
    return ranked[:top_k]


def format_rag_section(
    query: str,
    *,
    language: str = "uk",
    top_k: int = 5,
) -> str:
    """Format retrieved chunks for injection into the LLM system prompt."""
    chunks = retrieve(query, language=language, top_k=top_k, min_score=0.5)
    if not chunks:
        # Always include dispatcher triage baseline
        chunks = retrieve("dispatcher priority protocol", top_k=2, min_score=0)

    header = "## RAG — релевантні протоколи" if language == "uk" else "## RAG — relevant protocols"
    lines = [header]
    for chunk in chunks:
        lines.append(f"\n### [{chunk.category}] {chunk.id} (score={chunk.score:.1f})")
        lines.append(chunk.text(language))
    return "\n".join(lines)


def build_statistical_chunks(
    risk_brief: Dict[str, Any],
    *,
    language: str = "uk",
) -> str:
    """Turn computed risk statistics into a retrievable-style context block."""
    if not risk_brief:
        return ""

    is_uk = language == "uk"
    lines = [
        "## RAG — статистика та прогноз" if is_uk else "## RAG — statistics & forecast",
        f"Область: {risk_brief.get('region_name', '?')}" if is_uk
        else f"Oblast: {risk_brief.get('region_name', '?')}",
        f"Поточний статус: {risk_brief.get('current_status', '?')}" if is_uk
        else f"Current status: {risk_brief.get('current_status', '?')}",
    ]

    if risk_brief.get("active_now"):
        lines.append("⚠️ Активна тривога зараз — статистика вторинна." if is_uk
                     else "⚠️ Active alarm now — statistics are secondary.")

    peak_hours = risk_brief.get("peak_hours") or []
    if peak_hours:
        label = "Години підвищеного ризику (30 днів)" if is_uk else "Elevated-risk hours (30d)"
        lines.append(f"{label}: {', '.join(str(h) for h in peak_hours)}")

    dow = risk_brief.get("peak_weekdays") or []
    if dow:
        label = "Дні підвищеного ризику" if is_uk else "Elevated-risk weekdays"
        lines.append(f"{label}: {', '.join(str(d) for d in dow)}")

    prob = risk_brief.get("next_6h_probability")
    if prob is not None:
        label = "Ймовірність тривоги наступні 6 год" if is_uk else "Alarm probability next 6 hours"
        lines.append(f"{label}: {prob}% ({risk_brief.get('risk_level', 'unknown')})")

    recent = risk_brief.get("recent_events") or []
    if recent:
        label = "Останні тривоги в області" if is_uk else "Recent alarms in oblast"
        lines.append(label + ":")
        for ev in recent[:5]:
            lines.append(f"  • {ev}")

    note = risk_brief.get("disclaimer")
    if note:
        lines.append(note)

    return "\n".join(lines)
