from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.marriage_update_date_request import MarriageUpdateDateRequest
    from ..models.marriage_update_where_request import MarriageUpdateWhereRequest


T = TypeVar("T", bound="MarriageUpdateRequest")


@_attrs_define
class MarriageUpdateRequest:
    """
    Attributes:
        data (MarriageUpdateDateRequest):
        where (MarriageUpdateWhereRequest):
    """

    data: MarriageUpdateDateRequest
    where: MarriageUpdateWhereRequest
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = self.data.to_dict()

        where = self.where.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
                "where": where,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.marriage_update_date_request import MarriageUpdateDateRequest
        from ..models.marriage_update_where_request import MarriageUpdateWhereRequest

        d = dict(src_dict)
        data = MarriageUpdateDateRequest.from_dict(d.pop("data"))

        where = MarriageUpdateWhereRequest.from_dict(d.pop("where"))

        marriage_update_request = cls(
            data=data,
            where=where,
        )

        marriage_update_request.additional_properties = d
        return marriage_update_request

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
