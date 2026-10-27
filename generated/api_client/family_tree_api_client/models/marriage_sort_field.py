from enum import StrEnum


class MarriageSortField(StrEnum):
    DIVORCED_AT = "divorced_at"
    ID = "id"
    MARRIED_AT = "married_at"

    def __str__(self) -> str:
        return str(self.value)
