"""Rescue-dispatcher assessment: priority, steps, and emergency routing."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from regions_data import SLUG_TO_NAME_UK, SLUG_TO_NAME_EN
from risk_predictor import compute_risk_brief, regional_ranking

_PRIORITY_UK = {
    "critical": "🔴 КРИТИЧНО",
    "high": "🟠 ВИСОКИЙ",
    "watch": "🟡 УВАГА",
    "normal": "🟢 НОРМА",
}
_PRIORITY_EN = {
    "critical": "🔴 CRITICAL",
    "high": "🟠 HIGH",
    "watch": "🟡 WATCH",
    "normal": "🟢 NORMAL",
}


def _status_label(status: str, language: str) -> str:
    uk = {"active": "Повна тривога", "warning": "Часткова тривога", "clear": "Спокійно", "occupied": "Окуповано"}
    en = {"active": "Full alarm", "warning": "Partial alert", "clear": "Clear", "occupied": "Occupied"}
    return (uk if language == "uk" else en).get(status, status)


def assess_dispatch(
    *,
    region_slug: str,
    region_status: str,
    all_regions: List[Dict[str, str]],
    nearest_shelters: Optional[List[Dict[str, Any]]] = None,
    language: str = "uk",
) -> Dict[str, Any]:
    """Produce structured dispatcher assessment for RAG + API."""
    is_uk = language == "uk"
    risk = compute_risk_brief(region_slug, current_status=region_status, language=language)
    priorities = _PRIORITY_UK if is_uk else _PRIORITY_EN

    # Neighboring alarms
    active_neighbors = [
        r["nameUk" if is_uk else "nameEn"]
        for r in all_regions
        if r.get("id") != region_slug and r.get("status") in ("active", "warning")
    ]

    if region_status == "active":
        priority = "critical"
        steps_uk = [
            "Негайно прямуйте до найближчого укриття.",
            "Візьміть телефон, документи, воду.",
            "Не використовуйте ліфт. Допоможіть літнім і дітям.",
            "У сховищі — подалі від дверей і вікон.",
            "Поранення/пожежа — 112 або 101.",
        ]
        steps_en = [
            "Go to the nearest shelter immediately.",
            "Take phone, ID, water.",
            "Do not use elevators. Help elderly and children.",
            "In shelter — stay away from doors and windows.",
            "Injury/fire — 112 or 101.",
        ]
    elif region_status == "warning":
        priority = "high"
        steps_uk = [
            "Залишайтесь у приміщенні, підготуйте маршрут до укриття.",
            "Перевірте тривожну валізу та заряд телефону.",
            "Слідкуйте за оновленням статусу — можлива ескалація.",
        ]
        steps_en = [
            "Stay indoors; prepare route to shelter.",
            "Check go-bag and phone charge.",
            "Monitor status updates — escalation possible.",
        ]
    elif active_neighbors:
        priority = "watch"
        steps_uk = [
            f"У вашій області спокійно, але тривога в: {', '.join(active_neighbors[:5])}.",
            "Тримайте телефон напоготові, знайте маршрут до укриття.",
            "Уникайте непотрібних поїздок.",
        ]
        steps_en = [
            f"Your oblast is clear, but alarms in: {', '.join(active_neighbors[:5])}.",
            "Keep phone ready; know shelter route.",
            "Avoid unnecessary travel.",
        ]
    elif risk.get("risk_level") in ("high", "medium"):
        priority = "watch"
        steps_uk = [
            f"Статистично підвищений ризик ({risk.get('next_6h_probability')}%) на найближчі години.",
            "Підготуйте речі для швидкого переходу в укриття.",
            f"Пікові години: {', '.join(risk.get('peak_hours') or [])}.",
        ]
        steps_en = [
            f"Statistically elevated risk ({risk.get('next_6h_probability')}%) in coming hours.",
            "Prepare items for quick move to shelter.",
            f"Peak hours: {', '.join(risk.get('peak_hours') or [])}.",
        ]
    else:
        priority = "normal"
        steps_uk = [
            "Зараз тривоги немає. Тримайте тривожну валізу готовою.",
            "Перевірте найближче укриття на карті «Безпека».",
        ]
        steps_en = [
            "No alarm now. Keep go-bag ready.",
            "Check nearest shelter on the Safety map.",
        ]

    steps = steps_uk if is_uk else steps_en
    shelter_lines: List[str] = []
    if nearest_shelters:
        for s in nearest_shelters[:3]:
            dist = f" (~{s['distance_km']:.1f} км)" if s.get("distance_km") is not None else ""
            shelter_lines.append(f"{s.get('nameUk' if is_uk else 'nameEn', s.get('nameUk', '?'))}{dist}")

    return {
        "priority": priority,
        "priority_label": priorities[priority],
        "region_slug": region_slug,
        "region_name": SLUG_TO_NAME_UK.get(region_slug, region_slug) if is_uk else SLUG_TO_NAME_EN.get(region_slug, region_slug),
        "status": region_status,
        "status_label": _status_label(region_status, language),
        "steps": steps,
        "nearest_shelters": shelter_lines,
        "active_neighbors": active_neighbors,
        "risk": risk,
        "hot_regions": regional_ranking(language=language, top_n=3),
        "emergency_numbers": ["112", "101", "103"],
    }


def format_dispatch_section(assessment: Dict[str, Any], *, language: str = "uk") -> str:
    """Format dispatcher assessment for LLM context."""
    if not assessment:
        return ""

    is_uk = language == "uk"
    lines = [
        "## Диспетчерська оцінка (GuardianEye)" if is_uk else "## Dispatcher assessment (GuardianEye)",
        f"{assessment.get('priority_label', '?')} — {assessment.get('region_name', '?')} ({assessment.get('status_label', '?')})",
    ]

    for i, step in enumerate(assessment.get("steps") or [], 1):
        lines.append(f"{i}. {step}")

    shelters = assessment.get("nearest_shelters") or []
    if shelters:
        label = "Найближчі укриття" if is_uk else "Nearest shelters"
        lines.append(f"{label}: " + "; ".join(shelters))

    hot = assessment.get("hot_regions") or []
    if hot:
        label = "Області з найбільшою активністю (30д)" if is_uk else "Most active oblasts (30d)"
        parts = [f"{h['region_name']} ({h['count_30d']})" for h in hot]
        lines.append(f"{label}: {', '.join(parts)}")

    nums = ", ".join(assessment.get("emergency_numbers") or ["112"])
    lines.append(f"{'Екстрені номери' if is_uk else 'Emergency numbers'}: {nums}")
    return "\n".join(lines)
