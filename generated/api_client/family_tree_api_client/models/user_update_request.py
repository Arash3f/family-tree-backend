from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.user_update_date_request import UserUpdateDateRequest
    from ..models.user_update_where_request import UserUpdateWhereRequest


T = TypeVar("T", bound="UserUpdateRequest")


@_attrs_define
class UserUpdateRequest:
    """
    Attributes:
        data (UserUpdateDateRequest):
        where (UserUpdateWhereRequest):
    """

    data: UserUpdateDateRequest
    where: UserUpdateWhereRequest
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
        from ..models.user_update_date_request import UserUpdateDateRequest
        from ..models.user_update_where_request import UserUpdateWhereRequest

        d = dict(src_dict)
        data = UserUpdateDateRequest.from_dict(d.pop("data"))

        where = UserUpdateWhereRequest.from_dict(d.pop("where"))

        user_update_request = cls(
            data=data,
            where=where,
        )

        user_update_request.additional_properties = d
        return user_update_request

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
