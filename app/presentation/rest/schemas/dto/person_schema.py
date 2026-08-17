from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.entities.person import Gender, ParentRelationshipType
from app.domain.shared.dto.person_filter_dto import PersonSortField
from app.domain.shared.dto.sorter_dto import SortOrderField
from app.presentation.rest.schemas.dto.common import (
    IsoDate,
    PaginationRequestParams,
    RangeRequest,
    SortRequestParams,
)


class ParentLinkRequest(BaseModel):
    parent_id: UUID
    relationship_type: ParentRelationshipType = ParentRelationshipType.BIOLOGICAL


class PersonModel(BaseModel):
    id: UUID | None
    name: str
    gender: Gender
    birth_date: IsoDate | None = None
    death_date: IsoDate | None = None
    family_name: str | None = None
    birth_place: str | None = None
    death_place: str | None = None
    notes: str | None = None
    parents: list[ParentLinkRequest] = Field(default_factory=list)
    marriage_id: UUID | None = None
    photo_object_key: str | None = None
    photo_url: str | None = None


class _PersonUpdateDateRequest(BaseModel):
    name: str | None = None
    gender: Gender | None = None
    birth_date: IsoDate | None = None
    death_date: IsoDate | None = None
    family_name: str | None = None
    birth_place: str | None = None
    death_place: str | None = None
    notes: str | None = None
    parents: list[ParentLinkRequest] | None = None
    marriage_id: UUID | None = None
    photo_object_key: str | None = None


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
    family_name: str | None = None
    birth_place: str | None = None
    death_place: str | None = None
    notes: str | None = None
    parents: list[ParentLinkRequest] = Field(default_factory=list)
    marriage_id: UUID | None = None
    photo_object_key: str | None = None
    photo_url: str | None = None


class PersonGetResponse(BaseModel):
    id: UUID
    name: str
    gender: Gender
    birth_date: date | None
    death_date: date | None = None
    family_name: str | None = None
    birth_place: str | None = None
    death_place: str | None = None
    notes: str | None = None
    parents: list[ParentLinkRequest] = Field(default_factory=list)
    marriage_id: UUID | None = None
    photo_object_key: str | None = None
    photo_url: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Ali",
                "gender": "male",
                "birth_date": "1996-07-31",
            }
        }
    }


class PersonCreateRequest(BaseModel):
    name: str = Field(description="Person full name")
    gender: Gender
    birth_date: IsoDate | None = None
    death_date: IsoDate | None = None
    family_name: str | None = None
    birth_place: str | None = None
    death_place: str | None = None
    notes: str | None = None
    parents: list[ParentLinkRequest] = Field(default_factory=list)
    marriage_id: UUID | None = None
    photo_object_key: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "arash",
                "gender": "male",
                "birth_date": "2000-11-21",
                "parents": [
                    {
                        "parent_id": "00000000-0000-0000-0000-000000000001",
                        "relationship_type": "biological",
                    },
                    {
                        "parent_id": "00000000-0000-0000-0000-000000000002",
                        "relationship_type": "biological",
                    },
                ],
            }
        }
    }


class PersonCreateResponse(BaseModel):
    id: UUID
    name: str
    gender: Gender
    birth_date: date | None
    death_date: date | None = None
    family_name: str | None = None
    birth_place: str | None = None
    death_place: str | None = None
    notes: str | None = None
    parents: list[ParentLinkRequest] = Field(default_factory=list)
    marriage_id: UUID | None = None
    photo_object_key: str | None = None
    photo_url: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "arash",
                "gender": "male",
                "birth_date": "2000-11-21",
                "parents": [
                    {
                        "parent_id": "00000000-0000-0000-0000-000000000001",
                        "relationship_type": "biological",
                    }
                ],
            }
        }
    }


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
    parent_id: UUID | None = None
    relationship_type: ParentRelationshipType | None = None
    marriage_id: UUID | None = None


class FilterPersonRequest(BaseModel):
    pagination: PaginationRequestParams = Field(default_factory=PaginationRequestParams)
    filters: PersonFilterRequestData | None = None
    sort: SortRequestParams[PersonSortField] = Field(
        default_factory=lambda: SortRequestParams(
            sort_order=SortOrderField.DESC,
            sort_by=PersonSortField.ID,
        )
    )
