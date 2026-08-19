from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types
from ..types import UNSET, Unset

T = TypeVar("T", bound="BodyImportExcelFamilyTreesTreeIdExcelImportPost")


@_attrs_define
class BodyImportExcelFamilyTreesTreeIdExcelImportPost:
    """
    Attributes:
        file (str):
        include (None | str | Unset):
    """

    file: str
    include: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file = self.file

        include: None | str | Unset
        if isinstance(self.include, Unset):
            include = UNSET
        else:
            include = self.include

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "file": file,
            }
        )
        if include is not UNSET:
            field_dict["include"] = include

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("file", (None, str(self.file).encode(), "text/plain")))

        if not isinstance(self.include, Unset):
            if isinstance(self.include, str):
                files.append(("include", (None, str(self.include).encode(), "text/plain")))
            else:
                files.append(("include", (None, str(self.include).encode(), "text/plain")))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file = d.pop("file")

        def _parse_include(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        include = _parse_include(d.pop("include", UNSET))

        body_import_excel_family_trees_tree_id_excel_import_post = cls(
            file=file,
            include=include,
        )

        body_import_excel_family_trees_tree_id_excel_import_post.additional_properties = d
        return body_import_excel_family_trees_tree_id_excel_import_post

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
