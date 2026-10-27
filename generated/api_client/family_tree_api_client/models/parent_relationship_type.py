from enum import StrEnum


class ParentRelationshipType(StrEnum):
    ADOPTIVE = "adoptive"
    BIOLOGICAL = "biological"
    STEP = "step"

    def __str__(self) -> str:
        return str(self.value)
