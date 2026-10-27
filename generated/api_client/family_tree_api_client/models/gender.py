from enum import StrEnum


class Gender(StrEnum):
    FEMALE = "female"
    MALE = "male"

    def __str__(self) -> str:
        return str(self.value)
