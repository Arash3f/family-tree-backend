from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.range_request import RangeRequest


T = TypeVar("T", bound="MarriageFilterRequestData")


@_attrs_define
class MarriageFilterRequestData:
    """
    Attributes:
        id (None | Unset | UUID):
        spouse_a_id (None | Unset | UUID):
        spouse_b_id (None | Unset | UUID):
        married_at (None | RangeRequest | Unset):
        divorced_at (None | RangeRequest | Unset):
    """

    id: None | Unset | UUID = UNSET
    spouse_a_id: None | Unset | UUID = UNSET
    spouse_b_id: None | Unset | UUID = UNSET
    married_at: None | RangeRequest | Unset = UNSET
    divorced_at: None | RangeRequest | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.range_request import RangeRequest

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        elif isinstance(self.id, UUID):
            id = str(self.id)
        else:
            id = self.id

        spouse_a_id: None | str | Unset
        if isinstance(self.spouse_a_id, Unset):
            spouse_a_id = UNSET
        elif isinstance(self.spouse_a_id, UUID):
            spouse_a_id = str(self.spouse_a_id)
        else:
            spouse_a_id = self.spouse_a_id

        spouse_b_id: None | str | Unset
        if isinstance(self.spouse_b_id, Unset):
            spouse_b_id = UNSET
        elif isinstance(self.spouse_b_id, UUID):
            spouse_b_id = str(self.spouse_b_id)
        else:
            spouse_b_id = self.spouse_b_id

        married_at: dict[str, Any] | None | Unset
        if isinstance(self.married_at, Unset):
            married_at = UNSET
        elif isinstance(self.married_at, RangeRequest):
            married_at = self.married_at.to_dict()
        else:
            married_at = self.married_at

        divorced_at: dict[str, Any] | None | Unset
        if isinstance(self.divorced_at, Unset):
            divorced_at = UNSET
        elif isinstance(self.divorced_at, RangeRequest):
            divorced_at = self.divorced_at.to_dict()
        else:
            divorced_at = self.divorced_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if spouse_a_id is not UNSET:
            field_dict["spouse_a_id"] = spouse_a_id
        if spouse_b_id is not UNSET:
            field_dict["spouse_b_id"] = spouse_b_id
        if married_at is not UNSET:
            field_dict["married_at"] = married_at
        if divorced_at is not UNSET:
            field_dict["divorced_at"] = divorced_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.range_request import RangeRequest

        d = dict(src_dict)

        def _parse_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                id_type_0 = UUID(data)

                return id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_spouse_a_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                spouse_a_id_type_0 = UUID(data)

                return spouse_a_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        spouse_a_id = _parse_spouse_a_id(d.pop("spouse_a_id", UNSET))

        def _parse_spouse_b_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                spouse_b_id_type_0 = UUID(data)

                return spouse_b_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        spouse_b_id = _parse_spouse_b_id(d.pop("spouse_b_id", UNSET))

        def _parse_married_at(data: object) -> None | RangeRequest | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                married_at_type_0 = RangeRequest.from_dict(data)

                return married_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RangeRequest | Unset, data)

        married_at = _parse_married_at(d.pop("married_at", UNSET))

        def _parse_divorced_at(data: object) -> None | RangeRequest | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                divorced_at_type_0 = RangeRequest.from_dict(data)

                return divorced_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RangeRequest | Unset, data)

        divorced_at = _parse_divorced_at(d.pop("divorced_at", UNSET))

        marriage_filter_request_data = cls(
            id=id,
            spouse_a_id=spouse_a_id,
            spouse_b_id=spouse_b_id,
            married_at=married_at,
            divorced_at=divorced_at,
        )

        marriage_filter_request_data.additional_properties = d
        return marriage_filter_request_data

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
