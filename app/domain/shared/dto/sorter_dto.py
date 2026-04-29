from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel


class SortOrderField(str, Enum):
    DESC = "desc"
    ASC = "asc"


T = TypeVar("T")


class SortParams(BaseModel, Generic[T]):
    sort_order: SortOrderField
    sort_by: T
