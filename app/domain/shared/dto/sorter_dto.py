from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel


class SortOrderField(StrEnum):
    DESC = "desc"
    ASC = "asc"


T = TypeVar("T")


class SortParams(BaseModel, Generic[T]):
    sort_order: SortOrderField
    sort_by: T
