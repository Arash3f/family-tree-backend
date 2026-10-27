from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.relationship_path_item_response import RelationshipPathItemResponse


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
        label_fa (None | str | Unset):
        label_en (None | str | Unset):
        description_fa (None | str | Unset):
        description_en (None | str | Unset):
        paths (list[RelationshipPathItemResponse] | Unset):
    """

    from_person_id: UUID
    to_person_id: UUID
    found: bool
    distance: int | None | Unset = UNSET
    path_person_ids: list[UUID] | Unset = UNSET
    relationship_types: list[str] | Unset = UNSET
    label_fa: None | str | Unset = UNSET
    label_en: None | str | Unset = UNSET
    description_fa: None | str | Unset = UNSET
    description_en: None | str | Unset = UNSET
    paths: list[RelationshipPathItemResponse] | Unset = UNSET
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

        label_fa: None | str | Unset
        if isinstance(self.label_fa, Unset):
            label_fa = UNSET
        else:
            label_fa = self.label_fa

        label_en: None | str | Unset
        if isinstance(self.label_en, Unset):
            label_en = UNSET
        else:
            label_en = self.label_en

        description_fa: None | str | Unset
        if isinstance(self.description_fa, Unset):
            description_fa = UNSET
        else:
            description_fa = self.description_fa

        description_en: None | str | Unset
        if isinstance(self.description_en, Unset):
            description_en = UNSET
        else:
            description_en = self.description_en

        paths: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.paths, Unset):
            paths = []
            for paths_item_data in self.paths:
                paths_item = paths_item_data.to_dict()
                paths.append(paths_item)

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
        if label_fa is not UNSET:
            field_dict["label_fa"] = label_fa
        if label_en is not UNSET:
            field_dict["label_en"] = label_en
        if description_fa is not UNSET:
            field_dict["description_fa"] = description_fa
        if description_en is not UNSET:
            field_dict["description_en"] = description_en
        if paths is not UNSET:
            field_dict["paths"] = paths

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.relationship_path_item_response import RelationshipPathItemResponse  # noqa: PLC0415

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

        def _parse_label_fa(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        label_fa = _parse_label_fa(d.pop("label_fa", UNSET))

        def _parse_label_en(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        label_en = _parse_label_en(d.pop("label_en", UNSET))

        def _parse_description_fa(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description_fa = _parse_description_fa(d.pop("description_fa", UNSET))

        def _parse_description_en(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description_en = _parse_description_en(d.pop("description_en", UNSET))

        _paths = d.pop("paths", UNSET)
        paths: list[RelationshipPathItemResponse] | Unset = UNSET
        if _paths is not UNSET:
            paths = []
            for paths_item_data in _paths:
                paths_item = RelationshipPathItemResponse.from_dict(paths_item_data)

                paths.append(paths_item)

        closest_relationship_response = cls(
            from_person_id=from_person_id,
            to_person_id=to_person_id,
            found=found,
            distance=distance,
            path_person_ids=path_person_ids,
            relationship_types=relationship_types,
            label_fa=label_fa,
            label_en=label_en,
            description_fa=description_fa,
            description_en=description_en,
            paths=paths,
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
