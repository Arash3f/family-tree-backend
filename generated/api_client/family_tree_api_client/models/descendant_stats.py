from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.gender_counts import GenderCounts
    from ..models.generation_stats import GenerationStats


T = TypeVar("T", bound="DescendantStats")


@_attrs_define
class DescendantStats:
    """
    Attributes:
        generations (list[GenerationStats] | Unset):
        total (GenderCounts | Unset):
    """

    generations: list[GenerationStats] | Unset = UNSET
    total: GenderCounts | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        generations: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.generations, Unset):
            generations = []
            for generations_item_data in self.generations:
                generations_item = generations_item_data.to_dict()
                generations.append(generations_item)

        total: dict[str, Any] | Unset = UNSET
        if not isinstance(self.total, Unset):
            total = self.total.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if generations is not UNSET:
            field_dict["generations"] = generations
        if total is not UNSET:
            field_dict["total"] = total

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.gender_counts import GenderCounts  # noqa: PLC0415
        from ..models.generation_stats import GenerationStats  # noqa: PLC0415

        d = dict(src_dict)
        _generations = d.pop("generations", UNSET)
        generations: list[GenerationStats] | Unset = UNSET
        if _generations is not UNSET:
            generations = []
            for generations_item_data in _generations:
                generations_item = GenerationStats.from_dict(generations_item_data)

                generations.append(generations_item)

        _total = d.pop("total", UNSET)
        total: GenderCounts | Unset
        if isinstance(_total, Unset):
            total = UNSET
        else:
            total = GenderCounts.from_dict(_total)

        descendant_stats = cls(
            generations=generations,
            total=total,
        )

        descendant_stats.additional_properties = d
        return descendant_stats

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
