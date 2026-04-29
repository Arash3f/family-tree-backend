from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class RangeDTO(Generic[T]):
    min: T | None
    max: T | None
