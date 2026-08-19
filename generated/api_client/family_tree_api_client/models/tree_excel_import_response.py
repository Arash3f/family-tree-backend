from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="TreeExcelImportResponse")


@_attrs_define
class TreeExcelImportResponse:
    """
    Attributes:
        persons_created (int):
        marriages_created (int):
    """

    persons_created: int
    marriages_created: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        persons_created = self.persons_created

        marriages_created = self.marriages_created

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "persons_created": persons_created,
                "marriages_created": marriages_created,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        persons_created = d.pop("persons_created")

        marriages_created = d.pop("marriages_created")

        tree_excel_import_response = cls(
            persons_created=persons_created,
            marriages_created=marriages_created,
        )

        tree_excel_import_response.additional_properties = d
        return tree_excel_import_response

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
