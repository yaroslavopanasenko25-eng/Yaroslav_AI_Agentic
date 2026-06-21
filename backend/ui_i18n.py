"""UI strings for Jinja2 templates (Python-only presentation tier)."""

from __future__ import annotations

from typing import Any, Dict

STRINGS: Dict[str, Dict[str, str]] = {
    "uk": {
        "app_title": "Ukraine Alarm Shield",
        "dashboard": "Карта",
        "analysis": "Аналіз",
        "safety": "Безпека",
        "settings": "Налаштування",
        "close": "Закрити",
        "darkTheme": "Темна тема",
        "lightTheme": "Світла тема",
        "language": "Мова",
        "dyslexiaMode": "Режим дислексії",
        "aiAssistant": "ШІ Помічник",
        "typeMessage": "Напишіть повідомлення…",
        "send": "Надіслати",
        "duration": "Тривалість",
        "minutes": "хв",
        "missiles": "Ракети",
        "drones": "Дрони",
        "destroyed": "Збито",
        "hit": "Влучання",
        "alarmHistory": "Історія тривог",
        "duringAlarm": "Під час тривоги",
        "afterAlarm": "Після відбою",
        "general": "Загальні поради",
        "safety_subtitle": "Правила безпеки та карта укриттів",
        "oblasts_alarm": "Областей з тривогою",
        "avg_duration": "Сер. тривалість (хв)",
        "danger_level": "Рівень небезпеки",
        "alerts_period": "Тривоги за період",
        "appearance": "ОФОРМЛЕННЯ",
        "theme": "Тема",
        "theme_desc": "Темна або світла",
        "lang_desc": "Мова інтерфейсу",
        "accessibility": "ДОСТУПНОСТЬ",
        "dyslexia_desc": "Шрифт OpenDyslexic",
        "about": "ПРО ЗАСТОСУНОК",
        "emergency_numbers": "Екстрені номери",
    },
    "en": {
        "app_title": "Ukraine Alarm Shield",
        "dashboard": "Map",
        "analysis": "Analysis",
        "safety": "Safety",
        "settings": "Settings",
        "close": "Close",
        "darkTheme": "Dark theme",
        "lightTheme": "Light theme",
        "language": "Language",
        "dyslexiaMode": "Dyslexia mode",
        "aiAssistant": "AI Assistant",
        "typeMessage": "Type a message…",
        "send": "Send",
        "duration": "Duration",
        "minutes": "min",
        "missiles": "Missiles",
        "drones": "Drones",
        "destroyed": "Destroyed",
        "hit": "Hits",
        "alarmHistory": "Alarm history",
        "duringAlarm": "During alarm",
        "afterAlarm": "After all-clear",
        "general": "General tips",
        "safety_subtitle": "Safety rules and shelter map",
        "oblasts_alarm": "Oblasts in alarm",
        "avg_duration": "Avg duration (min)",
        "danger_level": "Danger level",
        "alerts_period": "Alerts in period",
        "appearance": "APPEARANCE",
        "theme": "Theme",
        "theme_desc": "Dark or light",
        "lang_desc": "Interface language",
        "accessibility": "ACCESSIBILITY",
        "dyslexia_desc": "OpenDyslexic font",
        "about": "ABOUT",
        "emergency_numbers": "Emergency numbers",
    },
}


def t(key: str, lang: str = "uk") -> str:
    return STRINGS.get(lang, STRINGS["uk"]).get(key, key)


def period_labels(lang: str) -> Dict[str, Dict[str, str]]:
    if lang == "uk":
        return {
            "1h": {"btn": "1год", "total": "За годину"},
            "1d": {"btn": "1д", "total": "Сьогодні"},
            "7d": {"btn": "7д", "total": "За 7 днів"},
            "14d": {"btn": "14д", "total": "За 14 днів"},
            "30d": {"btn": "30д", "total": "За 30 днів"},
        }
    return {
        "1h": {"btn": "1H", "total": "Last hour"},
        "1d": {"btn": "1D", "total": "Today"},
        "7d": {"btn": "7D", "total": "Last 7 days"},
        "14d": {"btn": "14D", "total": "Last 14 days"},
        "30d": {"btn": "30D", "total": "Last 30 days"},
    }
