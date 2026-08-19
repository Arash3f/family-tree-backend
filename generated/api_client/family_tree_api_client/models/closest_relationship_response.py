from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ClosestRelationshipResponse")


@_attrs_define
class ClosestRelationshipResponse:
    """
    Attributes:
        from_person_id (UUID):
        to_person_id (UUID):
        found (bool):
        distance (int | None | Unset):
        path_person_ids (list[UUID] | Unset):
        relationship_types (list[str] | Unset):
    """

    from_person_id: UUID
    to_person_id: UUID
    found: bool
    distance: int | None | Unset = UNSET
    path_person_ids: list[UUID] | Unset = UNSET
    relationship_types: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from_person_id = str(self.from_person_id)

        to_person_id = str(self.to_person_id)

        found = self.found

        distance: int | None | Unset
        if isinstance(self.distance, Unset):
            distance = UNSET
        else:
            distance = self.distance

        path_person_ids: list[str] | Unset = UNSET
        if not isinstance(self.path_person_ids, Unset):
            path_person_ids = []
            for path_person_ids_item_data in self.path_person_ids:
                path_person_ids_item = str(path_person_ids_item_data)
                path_person_ids.append(path_person_ids_item)

        relationship_types: list[str] | Unset = UNSET
        if not isinstance(self.relationship_types, Unset):
            relationship_types = self.relationship_types

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "from_person_id": from_person_id,
                "to_person_id": to_person_id,
                "found": found,
            }
        )
        if distance is not UNSET:
            field_dict["distance"] = distance
        if path_person_ids is not UNSET:
            field_dict["path_person_ids"] = path_person_ids
        if relationship_types is not UNSET:
            field_dict["relationship_types"] = relationship_types

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        from_person_id = UUID(d.pop("from_person_id"))

        to_person_id = UUID(d.pop("to_person_id"))

        found = d.pop("found")

        def _parse_distance(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        distance = _parse_distance(d.pop("distance", UNSET))

        _path_person_ids = d.pop("path_person_ids", UNSET)
        path_person_ids: list[UUID] | Unset = UNSET
        if _path_person_ids is not UNSET:
            path_person_ids = []
            for path_person_ids_item_data in _path_person_ids:
                path_person_ids_item = UUID(path_person_ids_item_data)

                path_person_ids.append(path_person_ids_item)

        relationship_types = cast(list[str], d.pop("relationship_types", UNSET))

        closest_relationship_response = cls(
            from_person_id=from_person_id,
            to_person_id=to_person_id,
            found=found,
            distance=distance,
            path_person_ids=path_person_ids,
            relationship_types=relationship_types,
        )

        closest_relationship_response.additional_properties = d
        return closest_relationship_response

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
