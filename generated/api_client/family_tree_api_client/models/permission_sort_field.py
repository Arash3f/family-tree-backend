from enum import StrEnum


class PermissionSortField(StrEnum):
    ID = "id"
    NAME = "name"

    def __str__(self) -> str:
        return str(self.value)
