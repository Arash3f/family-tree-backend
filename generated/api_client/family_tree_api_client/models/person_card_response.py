from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.descendant_stats import DescendantStats
    from ..models.person_card_marriage import PersonCardMarriage
    from ..models.person_card_parent import PersonCardParent
    from ..models.person_get_response import PersonGetResponse


T = TypeVar("T", bound="PersonCardResponse")


@_attrs_define
class PersonCardResponse:
    """
    Attributes:
        person (PersonGetResponse):  Example: {'birth_date': '1996-07-31', 'gender': 'male', 'name': 'Ali'}.
        parents (list[PersonCardParent] | Unset):
        marriages (list[PersonCardMarriage] | Unset):
        descendants (DescendantStats | Unset):
    """

    person: PersonGetResponse
    parents: list[PersonCardParent] | Unset = UNSET
    marriages: list[PersonCardMarriage] | Unset = UNSET
    descendants: DescendantStats | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        person = self.person.to_dict()

        parents: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.parents, Unset):
            parents = []
            for parents_item_data in self.parents:
                parents_item = parents_item_data.to_dict()
                parents.append(parents_item)

        marriages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.marriages, Unset):
            marriages = []
            for marriages_item_data in self.marriages:
                marriages_item = marriages_item_data.to_dict()
                marriages.append(marriages_item)

        descendants: dict[str, Any] | Unset = UNSET
        if not isinstance(self.descendants, Unset):
            descendants = self.descendants.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "person": person,
            }
        )
        if parents is not UNSET:
            field_dict["parents"] = parents
        if marriages is not UNSET:
            field_dict["marriages"] = marriages
        if descendants is not UNSET:
            field_dict["descendants"] = descendants

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.descendant_stats import DescendantStats  # noqa: PLC0415
        from ..models.person_card_marriage import PersonCardMarriage  # noqa: PLC0415
        from ..models.person_card_parent import PersonCardParent  # noqa: PLC0415
        from ..models.person_get_response import PersonGetResponse  # noqa: PLC0415

        d = dict(src_dict)
        person = PersonGetResponse.from_dict(d.pop("person"))

        _parents = d.pop("parents", UNSET)
        parents: list[PersonCardParent] | Unset = UNSET
        if _parents is not UNSET:
            parents = []
            for parents_item_data in _parents:
                parents_item = PersonCardParent.from_dict(parents_item_data)

                parents.append(parents_item)

        _marriages = d.pop("marriages", UNSET)
        marriages: list[PersonCardMarriage] | Unset = UNSET
        if _marriages is not UNSET:
            marriages = []
            for marriages_item_data in _marriages:
                marriages_item = PersonCardMarriage.from_dict(marriages_item_data)

                marriages.append(marriages_item)

        _descendants = d.pop("descendants", UNSET)
        descendants: DescendantStats | Unset
        if isinstance(_descendants, Unset):
            descendants = UNSET
        else:
            descendants = DescendantStats.from_dict(_descendants)

        person_card_response = cls(
            person=person,
            parents=parents,
            marriages=marriages,
            descendants=descendants,
        )

        person_card_response.additional_properties = d
        return person_card_response

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
