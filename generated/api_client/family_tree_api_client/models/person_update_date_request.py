from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.gender import Gender
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.parent_link_request import ParentLinkRequest


T = TypeVar("T", bound="PersonUpdateDateRequest")


@_attrs_define
class PersonUpdateDateRequest:
    """
    Attributes:
        name (None | str | Unset):
        gender (Gender | None | Unset):
        birth_date (datetime.date | None | Unset):
        death_date (datetime.date | None | Unset):
        family_name (None | str | Unset):
        birth_place (None | str | Unset):
        death_place (None | str | Unset):
        notes (None | str | Unset):
        parents (list[ParentLinkRequest] | None | Unset):
        marriage_id (None | Unset | UUID):
        photo_object_key (None | str | Unset):
    """

    name: None | str | Unset = UNSET
    gender: Gender | None | Unset = UNSET
    birth_date: datetime.date | None | Unset = UNSET
    death_date: datetime.date | None | Unset = UNSET
    family_name: None | str | Unset = UNSET
    birth_place: None | str | Unset = UNSET
    death_place: None | str | Unset = UNSET
    notes: None | str | Unset = UNSET
    parents: list[ParentLinkRequest] | None | Unset = UNSET
    marriage_id: None | Unset | UUID = UNSET
    photo_object_key: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
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

        birth_date: None | str | Unset
        if isinstance(self.birth_date, Unset):
            birth_date = UNSET
        elif isinstance(self.birth_date, datetime.date):
            birth_date = self.birth_date.isoformat()
        else:
            birth_date = self.birth_date

        death_date: None | str | Unset
        if isinstance(self.death_date, Unset):
            death_date = UNSET
        elif isinstance(self.death_date, datetime.date):
            death_date = self.death_date.isoformat()
        else:
            death_date = self.death_date

        family_name: None | str | Unset
        if isinstance(self.family_name, Unset):
            family_name = UNSET
        else:
            family_name = self.family_name

        birth_place: None | str | Unset
        if isinstance(self.birth_place, Unset):
            birth_place = UNSET
        else:
            birth_place = self.birth_place

        death_place: None | str | Unset
        if isinstance(self.death_place, Unset):
            death_place = UNSET
        else:
            death_place = self.death_place

        notes: None | str | Unset
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        parents: list[dict[str, Any]] | None | Unset
        if isinstance(self.parents, Unset):
            parents = UNSET
        elif isinstance(self.parents, list):
            parents = []
            for parents_type_0_item_data in self.parents:
                parents_type_0_item = parents_type_0_item_data.to_dict()
                parents.append(parents_type_0_item)

        else:
            parents = self.parents

        marriage_id: None | str | Unset
        if isinstance(self.marriage_id, Unset):
            marriage_id = UNSET
        elif isinstance(self.marriage_id, UUID):
            marriage_id = str(self.marriage_id)
        else:
            marriage_id = self.marriage_id

        photo_object_key: None | str | Unset
        if isinstance(self.photo_object_key, Unset):
            photo_object_key = UNSET
        else:
            photo_object_key = self.photo_object_key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if gender is not UNSET:
            field_dict["gender"] = gender
        if birth_date is not UNSET:
            field_dict["birth_date"] = birth_date
        if death_date is not UNSET:
            field_dict["death_date"] = death_date
        if family_name is not UNSET:
            field_dict["family_name"] = family_name
        if birth_place is not UNSET:
            field_dict["birth_place"] = birth_place
        if death_place is not UNSET:
            field_dict["death_place"] = death_place
        if notes is not UNSET:
            field_dict["notes"] = notes
        if parents is not UNSET:
            field_dict["parents"] = parents
        if marriage_id is not UNSET:
            field_dict["marriage_id"] = marriage_id
        if photo_object_key is not UNSET:
            field_dict["photo_object_key"] = photo_object_key

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.parent_link_request import ParentLinkRequest

        d = dict(src_dict)

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

        def _parse_birth_date(data: object) -> datetime.date | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                birth_date_type_0 = datetime.date.fromisoformat(data)

                return birth_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None | Unset, data)

        birth_date = _parse_birth_date(d.pop("birth_date", UNSET))

        def _parse_death_date(data: object) -> datetime.date | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                death_date_type_0 = datetime.date.fromisoformat(data)

                return death_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None | Unset, data)

        death_date = _parse_death_date(d.pop("death_date", UNSET))

        def _parse_family_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        family_name = _parse_family_name(d.pop("family_name", UNSET))

        def _parse_birth_place(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        birth_place = _parse_birth_place(d.pop("birth_place", UNSET))

        def _parse_death_place(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        death_place = _parse_death_place(d.pop("death_place", UNSET))

        def _parse_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        def _parse_parents(data: object) -> list[ParentLinkRequest] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                parents_type_0 = []
                _parents_type_0 = data
                for parents_type_0_item_data in _parents_type_0:
                    parents_type_0_item = ParentLinkRequest.from_dict(parents_type_0_item_data)

                    parents_type_0.append(parents_type_0_item)

                return parents_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ParentLinkRequest] | None | Unset, data)

        parents = _parse_parents(d.pop("parents", UNSET))

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

        def _parse_photo_object_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        photo_object_key = _parse_photo_object_key(d.pop("photo_object_key", UNSET))

        person_update_date_request = cls(
            name=name,
            gender=gender,
            birth_date=birth_date,
            death_date=death_date,
            family_name=family_name,
            birth_place=birth_place,
            death_place=death_place,
            notes=notes,
            parents=parents,
            marriage_id=marriage_id,
            photo_object_key=photo_object_key,
        )

        person_update_date_request.additional_properties = d
        return person_update_date_request

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
