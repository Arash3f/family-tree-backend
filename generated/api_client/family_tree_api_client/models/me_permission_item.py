from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MePermissionItem")


@_attrs_define
class MePermissionItem:
    """
    Attributes:
        name (str):
        description_en (str | Unset):  Default: ''.
        description_fa (str | Unset):  Default: ''.
    """

    name: str
    description_en: str | Unset = ""
    description_fa: str | Unset = ""
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description_en = self.description_en

        description_fa = self.description_fa

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if description_en is not UNSET:
            field_dict["description_en"] = description_en
        if description_fa is not UNSET:
            field_dict["description_fa"] = description_fa

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        description_en = d.pop("description_en", UNSET)

        description_fa = d.pop("description_fa", UNSET)

        me_permission_item = cls(
            name=name,
            description_en=description_en,
            description_fa=description_fa,
        )

        me_permission_item.additional_properties = d
        return me_permission_item

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
