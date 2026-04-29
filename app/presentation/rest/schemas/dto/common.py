from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel, field_validator

from app.domain.shared.dto.sorter_dto import SortOrderField
from app.presentation.utils.date_convert import jalali_to_gregorian


@dataclass
class IdRequest:
    id: int


@dataclass
class ResultResponse:
    result: str


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class PaginationRequestParams(BaseModel):
    page: int
    page_size: int
    offset: int


class SortRequestParams(BaseModel, Generic[T]):
    sort_order: SortOrderField
    sort_by: T


@dataclass
class RangeRequest(Generic[T]):
    min: T | None = None
    max: T | None = None

    @field_validator("min", mode="before")
    def parse_jalali_min(cls, v):
        if isinstance(v, str):
            return jalali_to_gregorian(v)
        return v

    @field_validator("max", mode="before")
    def parse_jalali_max(cls, v):
        if isinstance(v, str):
            return jalali_to_gregorian(v)
        return v
