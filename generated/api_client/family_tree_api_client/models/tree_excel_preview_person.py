from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TreeExcelPreviewPerson")


@_attrs_define
class TreeExcelPreviewPerson:
    """
    Attributes:
        ref (str):
        name (str):
        gender (str):
        row_number (int):
        family_name (None | str | Unset):
        birth_date (None | str | Unset):
        death_date (None | str | Unset):
        parent1_ref (None | str | Unset):
        parent2_ref (None | str | Unset):
        marriage_ref (None | str | Unset):
        already_exists (bool | Unset):  Default: False.
        existing_label (None | str | Unset):
        duplicate_of_ref (None | str | Unset):
    """

    ref: str
    name: str
    gender: str
    row_number: int
    family_name: None | str | Unset = UNSET
    birth_date: None | str | Unset = UNSET
    death_date: None | str | Unset = UNSET
    parent1_ref: None | str | Unset = UNSET
    parent2_ref: None | str | Unset = UNSET
    marriage_ref: None | str | Unset = UNSET
    already_exists: bool | Unset = False
    existing_label: None | str | Unset = UNSET
    duplicate_of_ref: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ref = self.ref

        name = self.name

        gender = self.gender

        row_number = self.row_number

        family_name: None | str | Unset
        if isinstance(self.family_name, Unset):
            family_name = UNSET
        else:
            family_name = self.family_name

        birth_date: None | str | Unset
        if isinstance(self.birth_date, Unset):
            birth_date = UNSET
        else:
            birth_date = self.birth_date

        death_date: None | str | Unset
        if isinstance(self.death_date, Unset):
            death_date = UNSET
        else:
            death_date = self.death_date

        parent1_ref: None | str | Unset
        if isinstance(self.parent1_ref, Unset):
            parent1_ref = UNSET
        else:
            parent1_ref = self.parent1_ref

        parent2_ref: None | str | Unset
        if isinstance(self.parent2_ref, Unset):
            parent2_ref = UNSET
        else:
            parent2_ref = self.parent2_ref

        marriage_ref: None | str | Unset
        if isinstance(self.marriage_ref, Unset):
            marriage_ref = UNSET
        else:
            marriage_ref = self.marriage_ref

        already_exists = self.already_exists

        existing_label: None | str | Unset
        if isinstance(self.existing_label, Unset):
            existing_label = UNSET
        else:
            existing_label = self.existing_label

        duplicate_of_ref: None | str | Unset
        if isinstance(self.duplicate_of_ref, Unset):
            duplicate_of_ref = UNSET
        else:
            duplicate_of_ref = self.duplicate_of_ref

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "ref": ref,
                "name": name,
                "gender": gender,
                "row_number": row_number,
            }
        )
        if family_name is not UNSET:
            field_dict["family_name"] = family_name
        if birth_date is not UNSET:
            field_dict["birth_date"] = birth_date
        if death_date is not UNSET:
            field_dict["death_date"] = death_date
        if parent1_ref is not UNSET:
            field_dict["parent1_ref"] = parent1_ref
        if parent2_ref is not UNSET:
            field_dict["parent2_ref"] = parent2_ref
        if marriage_ref is not UNSET:
            field_dict["marriage_ref"] = marriage_ref
        if already_exists is not UNSET:
            field_dict["already_exists"] = already_exists
        if existing_label is not UNSET:
            field_dict["existing_label"] = existing_label
        if duplicate_of_ref is not UNSET:
            field_dict["duplicate_of_ref"] = duplicate_of_ref

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ref = d.pop("ref")

        name = d.pop("name")

        gender = d.pop("gender")

        row_number = d.pop("row_number")

        def _parse_family_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        family_name = _parse_family_name(d.pop("family_name", UNSET))

        def _parse_birth_date(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        birth_date = _parse_birth_date(d.pop("birth_date", UNSET))

        def _parse_death_date(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        death_date = _parse_death_date(d.pop("death_date", UNSET))

        def _parse_parent1_ref(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        parent1_ref = _parse_parent1_ref(d.pop("parent1_ref", UNSET))

        def _parse_parent2_ref(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        parent2_ref = _parse_parent2_ref(d.pop("parent2_ref", UNSET))

        def _parse_marriage_ref(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        marriage_ref = _parse_marriage_ref(d.pop("marriage_ref", UNSET))

        already_exists = d.pop("already_exists", UNSET)

        def _parse_existing_label(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        existing_label = _parse_existing_label(d.pop("existing_label", UNSET))

        def _parse_duplicate_of_ref(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        duplicate_of_ref = _parse_duplicate_of_ref(d.pop("duplicate_of_ref", UNSET))

        tree_excel_preview_person = cls(
            ref=ref,
            name=name,
            gender=gender,
            row_number=row_number,
            family_name=family_name,
            birth_date=birth_date,
            death_date=death_date,
            parent1_ref=parent1_ref,
            parent2_ref=parent2_ref,
            marriage_ref=marriage_ref,
            already_exists=already_exists,
            existing_label=existing_label,
            duplicate_of_ref=duplicate_of_ref,
        )

        tree_excel_preview_person.additional_properties = d
        return tree_excel_preview_person

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
