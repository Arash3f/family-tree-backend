from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.gender import Gender
from ..types import UNSET, Unset

T = TypeVar("T", bound="PersonCardSummary")


@_attrs_define
class PersonCardSummary:
    """
    Attributes:
        id (UUID):
        name (str):
        gender (Gender):
        family_name (None | str | Unset):
        birth_date (datetime.date | None | Unset):
        death_date (datetime.date | None | Unset):
        photo_url (None | str | Unset):
    """

    id: UUID
    name: str
    gender: Gender
    family_name: None | str | Unset = UNSET
    birth_date: datetime.date | None | Unset = UNSET
    death_date: datetime.date | None | Unset = UNSET
    photo_url: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        gender = self.gender.value

        family_name: None | str | Unset
        if isinstance(self.family_name, Unset):
            family_name = UNSET
        else:
            family_name = self.family_name

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

        photo_url: None | str | Unset
        if isinstance(self.photo_url, Unset):
            photo_url = UNSET
        else:
            photo_url = self.photo_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "gender": gender,
            }
        )
        if family_name is not UNSET:
            field_dict["family_name"] = family_name
        if birth_date is not UNSET:
            field_dict["birth_date"] = birth_date
        if death_date is not UNSET:
            field_dict["death_date"] = death_date
        if photo_url is not UNSET:
            field_dict["photo_url"] = photo_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        gender = Gender(d.pop("gender"))

        def _parse_family_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        family_name = _parse_family_name(d.pop("family_name", UNSET))

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

        def _parse_photo_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        photo_url = _parse_photo_url(d.pop("photo_url", UNSET))

        person_card_summary = cls(
            id=id,
            name=name,
            gender=gender,
            family_name=family_name,
            birth_date=birth_date,
            death_date=death_date,
            photo_url=photo_url,
        )

        person_card_summary.additional_properties = d
        return person_card_summary

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
