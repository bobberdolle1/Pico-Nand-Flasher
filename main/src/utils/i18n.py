import json
import os
from typing import Dict


class I18n:
    """
    Internationalization for NAND Flasher with external JSON resources support.
    Looks for JSON files under src/resources/i18n and merges them over built-ins.
    """

    def __init__(self, default_lang: str = "en"):
        self.current_lang = default_lang
        self.translations: Dict[str, Dict[str, str]] = {}
        self._load_defaults()
        self._load_external_resources()

    def _load_defaults(self):
        # Minimal safe defaults; full dictionaries can be extended as needed
        self.translations["en"] = {
            "title": "NAND Flasher",
            "connect_button": "Connect",
            "disconnect_button": "Disconnect",
            "status_connected": "Connected",
            "status_disconnected": "Disconnected",
            "operations_select_dump": "Select Dump File",
            "nand_operations_read": "Read NAND",
            "nand_operations_write": "Write NAND",
            "nand_operations_erase": "Erase NAND",
        }
        self.translations["ru"] = {
            "title": "NAND Flasher",
            "connect_button": "Подключить",
            "disconnect_button": "Отключить",
            "status_connected": "Подключено",
            "status_disconnected": "Отключено",
            "operations_select_dump": "📂 Выбрать дамп",
            "nand_operations_read": "📥 Прочитать NAND",
            "nand_operations_write": "📤 Записать NAND",
            "nand_operations_erase": "🧹 Очистить NAND",
        }

    def _load_external_resources(self):
        # Compute resources directory: src/utils/i18n.py -> src/resources/i18n
        base_dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "resources", "i18n")
        )

        def _merge_lang(code: str, filename: str):
            path = os.path.join(base_dir, filename)
            if os.path.exists(path):
                try:
                    with open(path, encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            self.translations.setdefault(code, {})
                            self.translations[code].update(data)
                except Exception:
                    # Ignore malformed files; keep defaults
                    pass

        _merge_lang("en", "en.json")
        _merge_lang("ru", "ru.json")

    def set_language(self, lang: str):
        if lang in self.translations:
            self.current_lang = lang

    def t(self, key: str) -> str:
        # Return translation for current language, fallback to en, else key
        lang_map = self.translations.get(self.current_lang, {})
        if key in lang_map:
            return lang_map[key]
        return self.translations.get("en", {}).get(key, key)

    def get_available_languages(self) -> list:
        return list(self.translations.keys())


# Global singleton
i18n = I18n()
