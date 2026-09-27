from collections.abc import Mapping
from typing import Any

from app.domain.entities.family_tree import TreeMembership
from app.domain.shared.tree_access import TreeAccessPermissions


def redact_person_data(
    data: Mapping[str, Any], membership: TreeMembership
) -> dict[str, Any]:
    """Remove per-tree protected person fields from an API response."""
    result = dict(data)
    if not membership.has_access(TreeAccessPermissions.VIEW_BIRTH_DATE):
        result["birth_date"] = None
    if not membership.has_access(TreeAccessPermissions.VIEW_PHOTO):
        result["photo_object_key"] = None
        result["photo_url"] = None
    return result


def redact_person_summary(
    data: Mapping[str, Any] | None, membership: TreeMembership
) -> dict[str, Any] | None:
    if data is None:
        return None
    return redact_person_data(data, membership)


def redact_person_card(
    data: Mapping[str, Any], membership: TreeMembership
) -> dict[str, Any]:
    """Redact nested person/marriage fields on the person-card payload."""
    result = dict(data)
    result["person"] = redact_person_data(result.get("person") or {}, membership)

    parents = []
    for row in result.get("parents") or []:
        item = dict(row)
        item["person"] = redact_person_summary(item.get("person"), membership)
        parents.append(item)
    result["parents"] = parents

    marriages = []
    for row in result.get("marriages") or []:
        item = redact_marriage_data(row, membership)
        item["spouse"] = redact_person_summary(item.get("spouse"), membership)
        marriages.append(item)
    result["marriages"] = marriages

    descendants = dict(result.get("descendants") or {})
    generations = []
    for row in descendants.get("generations") or []:
        generation = dict(row)
        generation["people"] = [
            redact_person_data(person, membership)
            for person in generation.get("people") or []
        ]
        generations.append(generation)
    descendants["generations"] = generations
    result["descendants"] = descendants
    return result


def redact_marriage_data(
    data: Mapping[str, Any], membership: TreeMembership
) -> dict[str, Any]:
    """Remove per-tree protected marriage fields from an API response."""
    result = dict(data)
    if not membership.has_access(TreeAccessPermissions.VIEW_MARRIAGE_DATE):
        result["married_at"] = None
    return result
