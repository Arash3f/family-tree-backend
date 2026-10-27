from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GenderCounts")


@_attrs_define
class GenderCounts:
    """
    Attributes:
        male (int | Unset):  Default: 0.
        female (int | Unset):  Default: 0.
        total (int | Unset):  Default: 0.
    """

    male: int | Unset = 0
    female: int | Unset = 0
    total: int | Unset = 0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        male = self.male

        female = self.female

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if male is not UNSET:
            field_dict["male"] = male
        if female is not UNSET:
            field_dict["female"] = female
        if total is not UNSET:
            field_dict["total"] = total

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        male = d.pop("male", UNSET)

        female = d.pop("female", UNSET)

        total = d.pop("total", UNSET)

        gender_counts = cls(
            male=male,
            female=female,
            total=total,
        )

        gender_counts.additional_properties = d
        return gender_counts

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
