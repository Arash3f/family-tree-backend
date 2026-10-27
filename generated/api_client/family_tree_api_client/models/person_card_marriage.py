from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.person_card_summary import PersonCardSummary


T = TypeVar("T", bound="PersonCardMarriage")


@_attrs_define
class PersonCardMarriage:
    """
    Attributes:
        id (UUID):
        spouse_a_id (UUID):
        spouse_b_id (UUID):
        married_at (datetime.date | None | Unset):
        divorced_at (datetime.date | None | Unset):
        spouse (None | PersonCardSummary | Unset):
    """

    id: UUID
    spouse_a_id: UUID
    spouse_b_id: UUID
    married_at: datetime.date | None | Unset = UNSET
    divorced_at: datetime.date | None | Unset = UNSET
    spouse: None | PersonCardSummary | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.person_card_summary import PersonCardSummary  # noqa: PLC0415

        id = str(self.id)

        spouse_a_id = str(self.spouse_a_id)

        spouse_b_id = str(self.spouse_b_id)

        married_at: None | str | Unset
        if isinstance(self.married_at, Unset):
            married_at = UNSET
        elif isinstance(self.married_at, datetime.date):
            married_at = self.married_at.isoformat()
        else:
            married_at = self.married_at

        divorced_at: None | str | Unset
        if isinstance(self.divorced_at, Unset):
            divorced_at = UNSET
        elif isinstance(self.divorced_at, datetime.date):
            divorced_at = self.divorced_at.isoformat()
        else:
            divorced_at = self.divorced_at

        spouse: dict[str, Any] | None | Unset
        if isinstance(self.spouse, Unset):
            spouse = UNSET
        elif isinstance(self.spouse, PersonCardSummary):
            spouse = self.spouse.to_dict()
        else:
            spouse = self.spouse

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "spouse_a_id": spouse_a_id,
                "spouse_b_id": spouse_b_id,
            }
        )
        if married_at is not UNSET:
            field_dict["married_at"] = married_at
        if divorced_at is not UNSET:
            field_dict["divorced_at"] = divorced_at
        if spouse is not UNSET:
            field_dict["spouse"] = spouse

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.person_card_summary import PersonCardSummary  # noqa: PLC0415

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        spouse_a_id = UUID(d.pop("spouse_a_id"))

        spouse_b_id = UUID(d.pop("spouse_b_id"))

        def _parse_married_at(data: object) -> datetime.date | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                married_at_type_0 = datetime.date.fromisoformat(data)

                return married_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None | Unset, data)

        married_at = _parse_married_at(d.pop("married_at", UNSET))

        def _parse_divorced_at(data: object) -> datetime.date | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                divorced_at_type_0 = datetime.date.fromisoformat(data)

                return divorced_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None | Unset, data)

        divorced_at = _parse_divorced_at(d.pop("divorced_at", UNSET))

        def _parse_spouse(data: object) -> None | PersonCardSummary | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                spouse_type_0 = PersonCardSummary.from_dict(data)

                return spouse_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PersonCardSummary | Unset, data)

        spouse = _parse_spouse(d.pop("spouse", UNSET))

        person_card_marriage = cls(
            id=id,
            spouse_a_id=spouse_a_id,
            spouse_b_id=spouse_b_id,
            married_at=married_at,
            divorced_at=divorced_at,
            spouse=spouse,
        )

        person_card_marriage.additional_properties = d
        return person_card_marriage

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
