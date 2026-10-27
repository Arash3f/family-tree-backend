from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="KinshipLabelResponse")


@_attrs_define
class KinshipLabelResponse:
    """
    Attributes:
        label_fa (None | str): The relation's Persian name, e.g. پسرعمو
        label_en (None | str): The English name, e.g. paternal uncle's son
        description_fa (None | str): The chain word by word, in Persian
        description_en (None | str): The chain word by word, in English
    """

    label_fa: None | str
    label_en: None | str
    description_fa: None | str
    description_en: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        label_fa: None | str
        label_fa = self.label_fa

        label_en: None | str
        label_en = self.label_en

        description_fa: None | str
        description_fa = self.description_fa

        description_en: None | str
        description_en = self.description_en

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "label_fa": label_fa,
                "label_en": label_en,
                "description_fa": description_fa,
                "description_en": description_en,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_label_fa(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        label_fa = _parse_label_fa(d.pop("label_fa"))

        def _parse_label_en(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        label_en = _parse_label_en(d.pop("label_en"))

        def _parse_description_fa(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        description_fa = _parse_description_fa(d.pop("description_fa"))

        def _parse_description_en(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        description_en = _parse_description_en(d.pop("description_en"))

        kinship_label_response = cls(
            label_fa=label_fa,
            label_en=label_en,
            description_fa=description_fa,
            description_en=description_en,
        )

        kinship_label_response.additional_properties = d
        return kinship_label_response

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
