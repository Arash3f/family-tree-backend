from enum import StrEnum


class PreferredLocale(StrEnum):
    EN = "en"
    FA = "fa"


class PreferredTheme(StrEnum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"
