from enum import StrEnum


class GetDemoFamilyTreeFamilyTreesDemoGetLocale(StrEnum):
    EN = "en"
    FA = "fa"

    def __str__(self) -> str:
        return str(self.value)
