from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer, field_validator

from app.domain.entities.person import Gender
from app.domain.shared.dto.person_filter_dto import PersonSortField
from app.domain.shared.dto.sorter_dto import SortOrderField
from app.presentation.rest.schemas.dto.common import (
    PaginationRequestParams,
    RangeRequest,
    SortRequestParams,
)
from app.presentation.utils.date_convert import gregorian_to_jalali, jalali_to_gregorian


class PersonModel(BaseModel):
    id: UUID | None
    name: str
    gender: Gender
    birth_date: date | None = None
    death_date: date | None = None
    father_id: UUID | None = None
    mother_id: UUID | None = None

    @field_serializer("birth_date", "death_date")
    def serialize_jalali(self, v):
        if v is None:
            return None
        return gregorian_to_jalali(v)


class _PersonUpdateDateRequest(BaseModel):
    name: str | None = None
    gender: Gender | None = None
    birth_date: date | None = None
    death_date: date | None = None
    father_id: UUID | None = None
    mother_id: UUID | None = None

    @field_validator("birth_date", "death_date", mode="before")
    def parse_jalali(cls, v):
        if isinstance(v, str):
            return jalali_to_gregorian(v)
        return v


class _PersonUpdateWhereRequest(BaseModel):
    person_id: UUID


class PersonUpdateRequest(BaseModel):
    data: _PersonUpdateDateRequest
    where: _PersonUpdateWhereRequest


class PersonUpdateResponse(BaseModel):
    id: UUID
    name: str
    gender: Gender
    birth_date: date | None
    death_date: date | None = None
    father_id: UUID | None
    mother_id: UUID | None


class PersonGetResponse(BaseModel):
    id: UUID
    name: str
    gender: Gender
    birth_date: date | None
    death_date: date | None = None
    father_id: UUID | None
    mother_id: UUID | None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Ali",
                "gender": "male",
                "birth_date": "1375-05-10",
            }
        }
    }

    @field_serializer("birth_date", "death_date")
    def serialize_jalali(self, v):
        if v is None:
            return None
        return gregorian_to_jalali(v)


class PersonCreateRequest(BaseModel):
    name: str = Field(description="Person full name")
    gender: Gender
    birth_date: date | None = None
    death_date: date | None = None
    father_id: UUID | None = None
    mother_id: UUID | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "arash",
                "gender": "male",
                "birth_date": "1379/09/01",
                "father_id": "00000000-0000-0000-0000-000000000001",
                "mother_id": "00000000-0000-0000-0000-000000000002",
            }
        }
    }

    @field_validator("birth_date", "death_date", mode="before")
    def parse_jalali(cls, v):
        if isinstance(v, str):
            return jalali_to_gregorian(v)
        return v


class PersonCreateResponse(BaseModel):
    id: UUID
    name: str
    gender: Gender
    birth_date: date | None
    death_date: date | None = None
    father_id: UUID | None
    mother_id: UUID | None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "arash",
                "gender": "male",
                "birth_date": "1379/09/01",
                "father_id": "00000000-0000-0000-0000-000000000001",
                "mother_id": "00000000-0000-0000-0000-000000000002",
            }
        }
    }

    @field_serializer("birth_date", "death_date")
    def serialize_jalali(self, v):
        if v is None:
            return None
        return gregorian_to_jalali(v)


class ClosestRelationshipResponse(BaseModel):
    from_person_id: UUID
    to_person_id: UUID
    found: bool
    distance: int | None = None
    path_person_ids: list[UUID] = Field(default_factory=list)
    relationship_types: list[str] = Field(default_factory=list)


class PersonFilterRequestData(BaseModel):
    id: UUID | None = None
    name: str | None = None
    gender: Gender | None = None
    birth_date: RangeRequest[date] | None = None
    father_id: UUID | None = None
    mother_id: UUID | None = None


class FilterPersonRequest(BaseModel):
    pagination: PaginationRequestParams = Field(default_factory=PaginationRequestParams)
    filters: PersonFilterRequestData | None = None
    sort: SortRequestParams[PersonSortField] = Field(
        default_factory=lambda: SortRequestParams(
            sort_order=SortOrderField.DESC,
            sort_by=PersonSortField.ID,
        )
    )
