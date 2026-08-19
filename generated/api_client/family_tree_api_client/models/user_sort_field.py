from enum import Enum


class UserSortField(str, Enum):
    ID = "id"
    ROLE_ID = "role_id"
    USERNAME = "username"

    def __str__(self) -> str:
        return str(self.value)
