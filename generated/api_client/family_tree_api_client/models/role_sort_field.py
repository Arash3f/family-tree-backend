from enum import StrEnum


class RoleSortField(StrEnum):
    ID = "id"
    NAME = "name"

    def __str__(self) -> str:
        return str(self.value)
