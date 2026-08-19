from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TreeExcelPreviewMarriage")


@_attrs_define
class TreeExcelPreviewMarriage:
    """
    Attributes:
        ref (str):
        spouse_a_ref (str):
        spouse_b_ref (str):
        married_at (str):
        row_number (int):
        divorced_at (None | str | Unset):
        already_exists (bool | Unset):  Default: False.
        duplicate_of_ref (None | str | Unset):
        warning (None | str | Unset):
    """

    ref: str
    spouse_a_ref: str
    spouse_b_ref: str
    married_at: str
    row_number: int
    divorced_at: None | str | Unset = UNSET
    already_exists: bool | Unset = False
    duplicate_of_ref: None | str | Unset = UNSET
    warning: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ref = self.ref

        spouse_a_ref = self.spouse_a_ref

        spouse_b_ref = self.spouse_b_ref

        married_at = self.married_at

        row_number = self.row_number

        divorced_at: None | str | Unset
        if isinstance(self.divorced_at, Unset):
            divorced_at = UNSET
        else:
            divorced_at = self.divorced_at

        already_exists = self.already_exists

        duplicate_of_ref: None | str | Unset
        if isinstance(self.duplicate_of_ref, Unset):
            duplicate_of_ref = UNSET
        else:
            duplicate_of_ref = self.duplicate_of_ref

        warning: None | str | Unset
        if isinstance(self.warning, Unset):
            warning = UNSET
        else:
            warning = self.warning

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "ref": ref,
                "spouse_a_ref": spouse_a_ref,
                "spouse_b_ref": spouse_b_ref,
                "married_at": married_at,
                "row_number": row_number,
            }
        )
        if divorced_at is not UNSET:
            field_dict["divorced_at"] = divorced_at
        if already_exists is not UNSET:
            field_dict["already_exists"] = already_exists
        if duplicate_of_ref is not UNSET:
            field_dict["duplicate_of_ref"] = duplicate_of_ref
        if warning is not UNSET:
            field_dict["warning"] = warning

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ref = d.pop("ref")

        spouse_a_ref = d.pop("spouse_a_ref")

        spouse_b_ref = d.pop("spouse_b_ref")

        married_at = d.pop("married_at")

        row_number = d.pop("row_number")

        def _parse_divorced_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        divorced_at = _parse_divorced_at(d.pop("divorced_at", UNSET))

        already_exists = d.pop("already_exists", UNSET)

        def _parse_duplicate_of_ref(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        duplicate_of_ref = _parse_duplicate_of_ref(d.pop("duplicate_of_ref", UNSET))

        def _parse_warning(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        warning = _parse_warning(d.pop("warning", UNSET))

        tree_excel_preview_marriage = cls(
            ref=ref,
            spouse_a_ref=spouse_a_ref,
            spouse_b_ref=spouse_b_ref,
            married_at=married_at,
            row_number=row_number,
            divorced_at=divorced_at,
            already_exists=already_exists,
            duplicate_of_ref=duplicate_of_ref,
            warning=warning,
        )

        tree_excel_preview_marriage.additional_properties = d
        return tree_excel_preview_marriage

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
