from enum import StrEnum


class TreeMemberRole(StrEnum):
    MEMBER = "member"
    OWNER = "owner"

    def __str__(self) -> str:
        return str(self.value)
