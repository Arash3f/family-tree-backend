from enum import StrEnum


class KinshipStep(StrEnum):
    BROTHER = "brother"
    DAUGHTER = "daughter"
    FATHER = "father"
    HUSBAND = "husband"
    MOTHER = "mother"
    SISTER = "sister"
    SON = "son"
    WIFE = "wife"

    def __str__(self) -> str:
        return str(self.value)
