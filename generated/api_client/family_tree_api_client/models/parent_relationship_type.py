from enum import Enum


class ParentRelationshipType(str, Enum):
    ADOPTIVE = "adoptive"
    BIOLOGICAL = "biological"
    STEP = "step"

    def __str__(self) -> str:
        return str(self.value)
