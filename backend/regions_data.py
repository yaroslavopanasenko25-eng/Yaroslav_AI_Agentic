"""Shared Ukrainian region definitions and status builder."""

from __future__ import annotations

from typing import Dict, List

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

# Dashboard mock fallback (matches alarm-app/backend/index.js)
MOCK_STATUS: Dict[str, str] = {
    "donetsk": "active", "zaporizhzhia": "active", "sumy": "active", "kharkiv": "active",
    "dnipro": "warning", "kyiv-oblast": "warning", "kherson": "warning",
    "chernihiv": "warning", "kyiv-city": "warning",
    "luhansk": "occupied", "crimea": "occupied",
}


def build_regions(active_region_ids: set[str] | None = None, use_mock: bool = False) -> List[Dict[str, str]]:
    """Build the full region list with alarm statuses."""
    result = []
    for uid, slug, name_uk, name_en in ALL_REGIONS:
        if slug in OCCUPIED:
            status = "occupied"
        elif use_mock:
            status = MOCK_STATUS.get(slug, "clear")
        elif active_region_ids and (uid in active_region_ids or slug in active_region_ids):
            status = "active"
        else:
            status = "clear"
        result.append({"id": slug, "nameUk": name_uk, "nameEn": name_en, "status": status})
    return result
