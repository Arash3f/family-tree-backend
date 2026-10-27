from enum import StrEnum


class PersonSortField(StrEnum):
    BIRTH_DATE = "birth_date"
    GENDER = "gender"
    ID = "id"
    NAME = "name"

    def __str__(self) -> str:
        return str(self.value)
