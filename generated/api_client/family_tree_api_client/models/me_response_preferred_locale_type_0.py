from enum import StrEnum


class MeResponsePreferredLocaleType0(StrEnum):
    EN = "en"
    FA = "fa"

    def __str__(self) -> str:
        return str(self.value)
