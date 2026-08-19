from enum import Enum


class PersonSortField(str, Enum):
    BIRTH_DATE = "birth_date"
    GENDER = "gender"
    ID = "id"
    NAME = "name"

    def __str__(self) -> str:
        return str(self.value)
