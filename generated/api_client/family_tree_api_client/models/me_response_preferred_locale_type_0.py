from enum import Enum


class MeResponsePreferredLocaleType0(str, Enum):
    EN = "en"
    FA = "fa"

    def __str__(self) -> str:
        return str(self.value)
