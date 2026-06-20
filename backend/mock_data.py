"""Demo / fallback data used when Supabase or live APIs are unavailable."""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any, Dict, List

from regions_data import ALL_REGIONS, MOCK_STATUS

SAFETY_TIPS: Dict[str, List[Dict[str, str]]] = {
    "alarm": [
        {
            "id": "a1", "icon": "🏃",
            "titleUk": "Негайно йдіть до укриття", "titleEn": "Go to shelter immediately",
            "descUk": "Якщо є повітряна тривога — негайно перейдіть до найближчого бомбосховища або підвалу.",
            "descEn": "If an air alarm sounds, immediately proceed to the nearest bomb shelter or basement.",
        },
        {
            "id": "a2", "icon": "🪟",
            "titleUk": "Тримайтеся від вікон", "titleEn": "Stay away from windows",
            "descUk": "Не стійте біля вікон. Ударна хвиля може розбити скло і поранити.",
            "descEn": "Stay away from windows. A blast wave can shatter glass and cause injury.",
        },
        {
            "id": "a3", "icon": "📱",
            "titleUk": "Повідомте рідних", "titleEn": "Notify your family",
            "descUk": "Повідомте рідним де ви. Використовуйте месенджери, щоб не перевантажувати мережу.",
            "descEn": "Let family know your location. Use messengers to keep the network free.",
        },
        {
            "id": "a4", "icon": "🧳",
            "titleUk": "Тривожна валіза", "titleEn": "Emergency bag",
            "descUk": "Документи, вода, ліки, ліхтарик, заряджений телефон — завжди готові.",
            "descEn": "Documents, water, medicines, flashlight, charged phone — always ready.",
        },
    ],
    "after": [
        {
            "id": "p1", "icon": "✅",
            "titleUk": "Дочекайтеся відбою", "titleEn": "Wait for all-clear",
            "descUk": "Не виходьте до офіційного відбою. Загроза може тривати.",
            "descEn": "Do not leave until the official all-clear. The threat may continue.",
        },
        {
            "id": "p2", "icon": "🔍",
            "titleUk": "Перевірте оточення", "titleEn": "Check surroundings",
            "descUk": "Огляньте приміщення. Не торкайтеся підозрілих предметів.",
            "descEn": "Inspect the premises. Do not touch suspicious objects.",
        },
        {
            "id": "p3", "icon": "🆘",
            "titleUk": "Дзвоніть 101/112 при потребі", "titleEn": "Call 101/112 if needed",
            "descUk": "101 — пожежна, 103 — швидка, 112 — єдина екстрена допомога.",
            "descEn": "101 — fire, 103 — ambulance, 112 — unified emergency service.",
        },
    ],
    "general": [
        {
            "id": "g1", "icon": "💊",
            "titleUk": "Аптечка першої допомоги", "titleEn": "First aid kit",
            "descUk": "Бинти, джгути, знеболювальне, антисептик, серцеві ліки.",
            "descEn": "Bandages, tourniquets, painkillers, antiseptic, heart medications.",
        },
        {
            "id": "g2", "icon": "💧",
            "titleUk": "Запас води та їжі", "titleEn": "Water & food supply",
            "descUk": "3 л/добу на людину на 3–5 днів. Консерви та сухарі.",
            "descEn": "3L/day per person for 3–5 days. Canned goods and crackers.",
        },
        {
            "id": "g3", "icon": "🔦",
            "titleUk": "Автономне живлення", "titleEn": "Backup power",
            "descUk": "Павербанк, ліхтарик, резервна зарядка. Завжди заряджені.",
            "descEn": "Powerbank, flashlight, backup charger. Always charged.",
        },
        {
            "id": "g4", "icon": "📋",
            "titleUk": "Документи під рукою", "titleEn": "Documents at hand",
            "descUk": "Паспорт і медичні довідки у водонепроникному пакеті.",
            "descEn": "Passport and medical records in a waterproof bag.",
        },
    ],
}


def generate_mock_history(days: int = 14) -> List[Dict[str, Any]]:
    """Generate demo alarm history for the Analysis page."""
    region_ids = [slug for _, slug, _, _ in ALL_REGIONS if slug not in MOCK_STATUS or MOCK_STATUS.get(slug) != "occupied"]
    history: List[Dict[str, Any]] = []

    for i in range(days):
        day = date.today() - timedelta(days=i)
        alarms_count = random.randint(1, 8)
        day_regions = random.sample(region_ids, min(alarms_count, len(region_ids)))

        m_total = random.randint(2, 20)
        m_dest = int(m_total * (0.5 + random.random() * 0.4))
        m_hit = int((m_total - m_dest) * 0.55)
        m_lost = m_total - m_dest - m_hit

        d_total = random.randint(5, 50)
        d_dest = int(d_total * (0.55 + random.random() * 0.35))
        d_hit = int((d_total - d_dest) * 0.45)
        d_lost = d_total - d_dest - d_hit

        history.append({
            "id": f"alarm-{i}",
            "date": day.isoformat(),
            "startTime": f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}",
            "duration": random.randint(20, 200),
            "regions": day_regions,
            "threats": [
                {"type": "missiles", "total": m_total, "destroyed": m_dest, "hit": m_hit, "lost": m_lost},
                {"type": "drones", "total": d_total, "destroyed": d_dest, "hit": d_hit, "lost": d_lost},
            ],
        })

    return history
