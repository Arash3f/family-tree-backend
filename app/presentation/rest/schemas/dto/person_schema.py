from datetime import date

from pydantic import BaseModel, Field, field_serializer, field_validator

from app.domain.entities.person import Gender
from app.domain.shared.dto.person_filter_dto import PersonSortField
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    RangeRequest,
    SortRequestParams,
)
from app.presentation.utils.date_convert import gregorian_to_jalali, jalali_to_gregorian


class PersonModel(BaseModel):
    id: int | None
    name: str
    gender: Gender
    birth_date: date | None = None
    father_id: int | None = None
    mother_id: int | None = None

    @field_serializer("birth_date")
    def serialize_jalali(self, v):
        if v is None:
            return None
        return gregorian_to_jalali(v)


class _PersonUpdateDateRequest(BaseModel):
    name: str | None = None
    gender: Gender | None = None
    birth_date: date | None = None
    father_id: int | None = None
    mother_id: int | None = None

    @field_validator("birth_date", mode="before")
    def parse_jalali(cls, v):
        if isinstance(v, str):
            return jalali_to_gregorian(v)
        return v


class _PersonUpdateWhereRequest(BaseModel):
    person_id: int


class PersonUpdateRequest(BaseModel):
    data: _PersonUpdateDateRequest
    where: _PersonUpdateWhereRequest


class PersonUpdateResponse(BaseModel):
    id: int
    name: str
    gender: Gender
    birth_date: date | None
    father_id: int | None
    mother_id: int | None


class PersonGetResponse(BaseModel):
    id: int
    name: str
    gender: Gender
    birth_date: date | None
    father_id: int | None
    mother_id: int | None

    model_config = {
        "json_schema_extra": {
            "example": {
                "first_name": "Ali",
                "last_name": "Ahmadi",
                "birth_date": "1375-05-10",
            }
        }
    }

    @field_serializer("birth_date")
    def serialize_jalali(self, v):
        if v is None:
            return None
        return gregorian_to_jalali(v)


class PersonCreateRequest(BaseModel):
    name: str = Field(description="test")
    gender: Gender
    birth_date: date | None = None
    father_id: int | None = None
    mother_id: int | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "arash",
                "gender": "male",
                "birth_date": "1379/09/01",
                "father_id": 0,
                "mother_id": 0,
            }
        }
    }

    @field_validator("birth_date", mode="before")
    def parse_jalali(cls, v):
        if isinstance(v, str):
            return jalali_to_gregorian(v)
        return v


class PersonCreateResponse(BaseModel):
    id: int
    name: str
    gender: Gender
    birth_date: date | None
    father_id: int | None
    mother_id: int | None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "arash",
                "gender": "male",
                "birth_date": "1379/09/01",
                "father_id": 0,
                "mother_id": 0,
            }
        }
    }

    @field_serializer("birth_date")
    def serialize_jalali(self, v):
        if v is None:
            return None
        return gregorian_to_jalali(v)


class PersonFilterRequestData(BaseModel):
    id: int | None = None
    name: str | None = None
    gender: Gender | None = None
    birth_date: RangeRequest[date] | None = None
    father_id: int | None = None
    mother_id: int | None = None


class FilterPersonRequest(BaseModel):
    pagination: PaginationRequestParams
    filters: PersonFilterRequestData
    sort: SortRequestParams[PersonSortField]
