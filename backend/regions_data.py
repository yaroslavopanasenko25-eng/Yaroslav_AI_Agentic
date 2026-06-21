"""Shared Ukrainian region definitions and status builder."""

from __future__ import annotations

from typing import Dict, List, Set

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

UID_TO_SLUG: Dict[str, str] = {uid: slug for uid, slug, _, _ in ALL_REGIONS}
SLUG_TO_UID: Dict[str, str] = {slug: uid for uid, slug, _, _ in ALL_REGIONS}
SLUG_TO_NAME_UK: Dict[str, str] = {slug: name_uk for _, slug, name_uk, _ in ALL_REGIONS}
SLUG_TO_NAME_EN: Dict[str, str] = {slug: name_en for _, slug, _, name_en in ALL_REGIONS}

# IoT compact map order — https://devs.alerts.in.ua/ (/v1/iot/active_air_raid_alerts_by_oblast.json)
IOT_OBLAST_SLUGS: List[str] = [
    "crimea",
    "volyn",
    "vinnytsia",
    "dnipro",
    "donetsk",
    "zhytomyr",
    "zakarpattia",
    "zaporizhzhia",
    "ivano-frankivsk",
    "kyiv-city",
    "kyiv-oblast",
    "kirovohrad",
    "luhansk",
    "lviv",
    "mykolaiv",
    "odesa",
    "poltava",
    "rivne",
    "sevastopol",  # not on our map — ignored in build_regions
    "sumy",
    "ternopil",
    "kharkiv",
    "kherson",
    "khmelnytskyi",
    "cherkasy",
    "chernivtsi",
    "chernihiv",
]

# Official alerts.in.ua location UIDs — https://devs.alerts.in.ua/
API_OBLAST_UID_TO_SLUG: Dict[str, str] = {
    "3": "khmelnytskyi",
    "4": "vinnytsia",
    "5": "rivne",
    "8": "volyn",
    "9": "dnipro",
    "10": "zhytomyr",
    "11": "zakarpattia",
    "12": "zaporizhzhia",
    "13": "ivano-frankivsk",
    "14": "kyiv-oblast",
    "15": "kirovohrad",
    "16": "luhansk",
    "17": "mykolaiv",
    "18": "odesa",
    "19": "poltava",
    "20": "sumy",
    "21": "ternopil",
    "22": "kharkiv",
    "23": "kherson",
    "24": "cherkasy",
    "25": "chernihiv",
    "26": "chernivtsi",
    "27": "lviv",
    "28": "donetsk",
    "29": "crimea",
    "30": "sevastopol",
    "31": "kyiv-city",
}

# Dashboard mock fallback (matches alarm-app/backend/index.js)
MOCK_STATUS: Dict[str, str] = {
    "donetsk": "active", "zaporizhzhia": "active", "sumy": "active", "kharkiv": "active",
    "dnipro": "warning", "kyiv-oblast": "warning", "kherson": "warning",
    "chernihiv": "warning", "kyiv-city": "warning",
    "luhansk": "occupied", "crimea": "occupied",
}


def parse_iot_oblast_levels(status_line: str) -> Dict[str, str]:
    """Parse IoT oblast string → slug → code (A/P/N)."""
    levels: Dict[str, str] = {}
    line = status_line.strip().strip('"')
    for idx, code in enumerate(line):
        if idx >= len(IOT_OBLAST_SLUGS):
            break
        slug = IOT_OBLAST_SLUGS[idx]
        if slug == "sevastopol":
            continue
        levels[slug] = code if code in ("A", "P", "N") else "N"
    return levels


def parse_iot_oblast_status(status_line: str) -> tuple[Set[str], Set[str]]:
    """Parse IoT status string (A=full alert, P=partial, N=clear)."""
    active: Set[str] = set()
    warning: Set[str] = set()
    for slug, code in parse_iot_oblast_levels(status_line).items():
        if code == "A":
            active.add(slug)
        elif code == "P":
            warning.add(slug)
    return active, warning


def slug_from_alert(item: dict) -> str:
    """Resolve an alerts.in.ua record to our oblast slug."""
    location_type = str(item.get("location_type") or "").lower()
    oblast_uid = str(item.get("location_oblast_uid") or "")
    location_uid = str(item.get("location_uid") or "")

    if location_type == "oblast":
        if location_uid in API_OBLAST_UID_TO_SLUG:
            return API_OBLAST_UID_TO_SLUG[location_uid]
        if location_uid in UID_TO_SLUG:
            return UID_TO_SLUG[location_uid]

    if oblast_uid in API_OBLAST_UID_TO_SLUG:
        return API_OBLAST_UID_TO_SLUG[oblast_uid]

    oblast_title = str(item.get("location_oblast") or "")
    if oblast_title:
        matched = _slug_from_title(oblast_title)
        if matched:
            return matched

    title = str(item.get("location_title") or "")
    if title:
        matched = _slug_from_title(title)
        if matched:
            return matched

    return ""


def _slug_from_title(title: str) -> str:
    """Match Ukrainian oblast name fragment to slug."""
    t = title.lower().replace("'", "'")
    for slug, name_uk in SLUG_TO_NAME_UK.items():
        key = name_uk.lower().replace("область", "").replace("м. ", "").strip()
        if key and key in t:
            return slug
    if "київ" in t and "област" not in t:
        return "kyiv-city"
    if "київ" in t:
        return "kyiv-oblast"
    if "крим" in t:
        return "crimea"
    return ""


def alerts_to_region_status(alerts: list[dict]) -> tuple[set[str], set[str]]:
    """Map active.json alerts to oblast slugs (active / warning)."""
    active: set[str] = set()
    partial: set[str] = set()

    for item in alerts:
        slug = slug_from_alert(item)
        if not slug or slug in OCCUPIED:
            continue
        location_type = str(item.get("location_type") or "").lower()
        if location_type == "oblast":
            active.add(slug)
        else:
            partial.add(slug)

    partial -= active
    return active, partial


def build_regions_from_slugs(
    active_slugs: Set[str] | None = None,
    warning_slugs: Set[str] | None = None,
    use_mock: bool = False,
) -> List[Dict[str, str]]:
    """Build region list using slug sets (from IoT or active.json)."""
    active = active_slugs or set()
    warning = warning_slugs or set()
    result = []
    for _uid, slug, name_uk, name_en in ALL_REGIONS:
        if use_mock:
            status = MOCK_STATUS.get(slug, "clear")
        elif slug in OCCUPIED:
            status = "occupied"
        elif slug in active:
            status = "active"
        elif slug in warning:
            status = "warning"
        else:
            status = "clear"
        result.append({"id": slug, "nameUk": name_uk, "nameEn": name_en, "status": status})
    return result


def build_regions(
    active_region_ids: set[str] | None = None,
    warning_region_ids: set[str] | None = None,
    use_mock: bool = False,
) -> List[Dict[str, str]]:
    """Build the full region list with alarm statuses (legacy uid-based API)."""
    # Treat ids as slugs when they match known slugs
    active_slugs = {x for x in (active_region_ids or set()) if x in SLUG_TO_UID}
    warning_slugs = {x for x in (warning_region_ids or set()) if x in SLUG_TO_UID}
    for uid in active_region_ids or set():
        if uid in UID_TO_SLUG:
            active_slugs.add(UID_TO_SLUG[uid])
        if uid in API_OBLAST_UID_TO_SLUG:
            active_slugs.add(API_OBLAST_UID_TO_SLUG[uid])
    for uid in warning_region_ids or set():
        if uid in UID_TO_SLUG:
            warning_slugs.add(UID_TO_SLUG[uid])
        if uid in API_OBLAST_UID_TO_SLUG:
            warning_slugs.add(API_OBLAST_UID_TO_SLUG[uid])
    return build_regions_from_slugs(active_slugs, warning_slugs, use_mock=use_mock)
