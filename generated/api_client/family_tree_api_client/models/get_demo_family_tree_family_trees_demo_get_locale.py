from enum import Enum


class GetDemoFamilyTreeFamilyTreesDemoGetLocale(str, Enum):
    EN = "en"
    FA = "fa"

    def __str__(self) -> str:
        return str(self.value)
