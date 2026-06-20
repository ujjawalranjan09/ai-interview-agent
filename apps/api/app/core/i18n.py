"""Backend i18n utility for email templates and error messages."""
import json
import os
from typing import Optional

_translations: dict[str, dict[str, str]] = {}
_loaded = False


def _load_translations():
    global _translations, _loaded
    if _loaded:
        return
    locales_dir = os.path.join(os.path.dirname(__file__), "..", "locales")
    if not os.path.exists(locales_dir):
        _translations = {"en": {}}
        _loaded = True
        return
    for filename in os.listdir(locales_dir):
        if filename.endswith(".json"):
            locale = filename.replace(".json", "")
            with open(os.path.join(locales_dir, filename), "r", encoding="utf-8") as f:
                _translations[locale] = json.load(f)
    if "en" not in _translations:
        _translations["en"] = {}
    _loaded = True


def get_translation(key: str, locale: str = "en", default: Optional[str] = None) -> str:
    _load_translations()
    parts = key.split(".")
    translations = _translations.get(locale, _translations.get("en", {}))
    for part in parts:
        if isinstance(translations, dict):
            translations = translations.get(part, {})
        else:
            return default or key
    if isinstance(translations, str):
        return translations
    return default or key
