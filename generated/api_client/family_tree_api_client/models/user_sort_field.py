from enum import StrEnum


class UserSortField(StrEnum):
    ACCOUNT_TYPE = "account_type"
    EMAIL = "email"
    FULLNAME = "fullname"
    ID = "id"
    IS_ACTIVE = "is_active"
    LAST_SESSION_AT = "last_session_at"
    ROLE_ID = "role_id"
    USERNAME = "username"

    def __str__(self) -> str:
        return str(self.value)
