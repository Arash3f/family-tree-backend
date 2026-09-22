from enum import Enum


class UpdatePreferencesRequestPreferredThemeType0(str, Enum):
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"

    def __str__(self) -> str:
        return str(self.value)
