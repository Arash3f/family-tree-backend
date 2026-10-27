from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.parent_relationship_type import ParentRelationshipType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.person_card_summary import PersonCardSummary


T = TypeVar("T", bound="PersonCardParent")


@_attrs_define
class PersonCardParent:
    """
    Attributes:
        parent_id (UUID):
        relationship_type (ParentRelationshipType):
        person (None | PersonCardSummary | Unset):
    """

    parent_id: UUID
    relationship_type: ParentRelationshipType
    person: None | PersonCardSummary | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.person_card_summary import PersonCardSummary  # noqa: PLC0415

        parent_id = str(self.parent_id)

        relationship_type = self.relationship_type.value

        person: dict[str, Any] | None | Unset
        if isinstance(self.person, Unset):
            person = UNSET
        elif isinstance(self.person, PersonCardSummary):
            person = self.person.to_dict()
        else:
            person = self.person

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "parent_id": parent_id,
                "relationship_type": relationship_type,
            }
        )
        if person is not UNSET:
            field_dict["person"] = person

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.person_card_summary import PersonCardSummary  # noqa: PLC0415

        d = dict(src_dict)
        parent_id = UUID(d.pop("parent_id"))

        relationship_type = ParentRelationshipType(d.pop("relationship_type"))

        def _parse_person(data: object) -> None | PersonCardSummary | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                person_type_0 = PersonCardSummary.from_dict(data)

                return person_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PersonCardSummary | Unset, data)

        person = _parse_person(d.pop("person", UNSET))

        person_card_parent = cls(
            parent_id=parent_id,
            relationship_type=relationship_type,
            person=person,
        )

        person_card_parent.additional_properties = d
        return person_card_parent

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
