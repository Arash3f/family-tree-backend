from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RangeRequest")


@_attrs_define
class RangeRequest:
    """
    Attributes:
        min_ (datetime.date | None | Unset):
        max_ (datetime.date | None | Unset):
    """

    min_: datetime.date | None | Unset = UNSET
    max_: datetime.date | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        min_: None | str | Unset
        if isinstance(self.min_, Unset):
            min_ = UNSET
        elif isinstance(self.min_, datetime.date):
            min_ = self.min_.isoformat()
        else:
            min_ = self.min_

        max_: None | str | Unset
        if isinstance(self.max_, Unset):
            max_ = UNSET
        elif isinstance(self.max_, datetime.date):
            max_ = self.max_.isoformat()
        else:
            max_ = self.max_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if min_ is not UNSET:
            field_dict["min"] = min_
        if max_ is not UNSET:
            field_dict["max"] = max_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_min_(data: object) -> datetime.date | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                min_type_0 = datetime.date.fromisoformat(data)

                return min_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None | Unset, data)

        min_ = _parse_min_(d.pop("min", UNSET))

        def _parse_max_(data: object) -> datetime.date | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                max_type_0 = datetime.date.fromisoformat(data)

                return max_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None | Unset, data)

        max_ = _parse_max_(d.pop("max", UNSET))

        range_request = cls(
            min_=min_,
            max_=max_,
        )

        range_request.additional_properties = d
        return range_request

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
