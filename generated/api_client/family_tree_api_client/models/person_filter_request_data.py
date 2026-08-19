from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.gender import Gender
from ..models.parent_relationship_type import ParentRelationshipType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.range_request import RangeRequest


T = TypeVar("T", bound="PersonFilterRequestData")


@_attrs_define
class PersonFilterRequestData:
    """
    Attributes:
        id (None | Unset | UUID):
        name (None | str | Unset):
        gender (Gender | None | Unset):
        birth_date (None | RangeRequest | Unset):
        parent_id (None | Unset | UUID):
        relationship_type (None | ParentRelationshipType | Unset):
        marriage_id (None | Unset | UUID):
    """

    id: None | Unset | UUID = UNSET
    name: None | str | Unset = UNSET
    gender: Gender | None | Unset = UNSET
    birth_date: None | RangeRequest | Unset = UNSET
    parent_id: None | Unset | UUID = UNSET
    relationship_type: None | ParentRelationshipType | Unset = UNSET
    marriage_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.range_request import RangeRequest

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        elif isinstance(self.id, UUID):
            id = str(self.id)
        else:
            id = self.id

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        gender: None | str | Unset
        if isinstance(self.gender, Unset):
            gender = UNSET
        elif isinstance(self.gender, Gender):
            gender = self.gender.value
        else:
            gender = self.gender

        birth_date: dict[str, Any] | None | Unset
        if isinstance(self.birth_date, Unset):
            birth_date = UNSET
        elif isinstance(self.birth_date, RangeRequest):
            birth_date = self.birth_date.to_dict()
        else:
            birth_date = self.birth_date

        parent_id: None | str | Unset
        if isinstance(self.parent_id, Unset):
            parent_id = UNSET
        elif isinstance(self.parent_id, UUID):
            parent_id = str(self.parent_id)
        else:
            parent_id = self.parent_id

        relationship_type: None | str | Unset
        if isinstance(self.relationship_type, Unset):
            relationship_type = UNSET
        elif isinstance(self.relationship_type, ParentRelationshipType):
            relationship_type = self.relationship_type.value
        else:
            relationship_type = self.relationship_type

        marriage_id: None | str | Unset
        if isinstance(self.marriage_id, Unset):
            marriage_id = UNSET
        elif isinstance(self.marriage_id, UUID):
            marriage_id = str(self.marriage_id)
        else:
            marriage_id = self.marriage_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if gender is not UNSET:
            field_dict["gender"] = gender
        if birth_date is not UNSET:
            field_dict["birth_date"] = birth_date
        if parent_id is not UNSET:
            field_dict["parent_id"] = parent_id
        if relationship_type is not UNSET:
            field_dict["relationship_type"] = relationship_type
        if marriage_id is not UNSET:
            field_dict["marriage_id"] = marriage_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.range_request import RangeRequest

        d = dict(src_dict)

        def _parse_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                id_type_0 = UUID(data)

                return id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_gender(data: object) -> Gender | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                gender_type_0 = Gender(data)

                return gender_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(Gender | None | Unset, data)

        gender = _parse_gender(d.pop("gender", UNSET))

        def _parse_birth_date(data: object) -> None | RangeRequest | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                birth_date_type_0 = RangeRequest.from_dict(data)

                return birth_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RangeRequest | Unset, data)

        birth_date = _parse_birth_date(d.pop("birth_date", UNSET))

        def _parse_parent_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                parent_id_type_0 = UUID(data)

                return parent_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        parent_id = _parse_parent_id(d.pop("parent_id", UNSET))

        def _parse_relationship_type(data: object) -> None | ParentRelationshipType | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                relationship_type_type_0 = ParentRelationshipType(data)

                return relationship_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ParentRelationshipType | Unset, data)

        relationship_type = _parse_relationship_type(d.pop("relationship_type", UNSET))

        def _parse_marriage_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                marriage_id_type_0 = UUID(data)

                return marriage_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        marriage_id = _parse_marriage_id(d.pop("marriage_id", UNSET))

        person_filter_request_data = cls(
            id=id,
            name=name,
            gender=gender,
            birth_date=birth_date,
            parent_id=parent_id,
            relationship_type=relationship_type,
            marriage_id=marriage_id,
        )

        person_filter_request_data.additional_properties = d
        return person_filter_request_data

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
