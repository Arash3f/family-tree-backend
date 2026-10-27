from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.free_limits_response import FreeLimitsResponse
    from ..models.tree_usage_response import TreeUsageResponse


T = TypeVar("T", bound="UsageResponse")


@_attrs_define
class UsageResponse:
    """
    Attributes:
        account_type (str):
        limited (bool): Whether the free quotas apply right now.
        free_limits (FreeLimitsResponse):
        owned_trees (int):
        trees (list[TreeUsageResponse]):
        paid_until (datetime.date | None | Unset):
        days_left (int | None | Unset): Days the paid plan still covers, today included.
    """

    account_type: str
    limited: bool
    free_limits: FreeLimitsResponse
    owned_trees: int
    trees: list[TreeUsageResponse]
    paid_until: datetime.date | None | Unset = UNSET
    days_left: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        account_type = self.account_type

        limited = self.limited

        free_limits = self.free_limits.to_dict()

        owned_trees = self.owned_trees

        trees = []
        for trees_item_data in self.trees:
            trees_item = trees_item_data.to_dict()
            trees.append(trees_item)

        paid_until: None | str | Unset
        if isinstance(self.paid_until, Unset):
            paid_until = UNSET
        elif isinstance(self.paid_until, datetime.date):
            paid_until = self.paid_until.isoformat()
        else:
            paid_until = self.paid_until

        days_left: int | None | Unset
        if isinstance(self.days_left, Unset):
            days_left = UNSET
        else:
            days_left = self.days_left

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "account_type": account_type,
                "limited": limited,
                "free_limits": free_limits,
                "owned_trees": owned_trees,
                "trees": trees,
            }
        )
        if paid_until is not UNSET:
            field_dict["paid_until"] = paid_until
        if days_left is not UNSET:
            field_dict["days_left"] = days_left

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.free_limits_response import FreeLimitsResponse  # noqa: PLC0415
        from ..models.tree_usage_response import TreeUsageResponse  # noqa: PLC0415

        d = dict(src_dict)
        account_type = d.pop("account_type")

        limited = d.pop("limited")

        free_limits = FreeLimitsResponse.from_dict(d.pop("free_limits"))

        owned_trees = d.pop("owned_trees")

        trees = []
        _trees = d.pop("trees")
        for trees_item_data in _trees:
            trees_item = TreeUsageResponse.from_dict(trees_item_data)

            trees.append(trees_item)

        def _parse_paid_until(data: object) -> datetime.date | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                paid_until_type_0 = datetime.date.fromisoformat(data)

                return paid_until_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None | Unset, data)

        paid_until = _parse_paid_until(d.pop("paid_until", UNSET))

        def _parse_days_left(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        days_left = _parse_days_left(d.pop("days_left", UNSET))

        usage_response = cls(
            account_type=account_type,
            limited=limited,
            free_limits=free_limits,
            owned_trees=owned_trees,
            trees=trees,
            paid_until=paid_until,
            days_left=days_left,
        )

        usage_response.additional_properties = d
        return usage_response

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
