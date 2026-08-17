from typing import Any

from collections.abc import Mapping

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


def redact_marriage_data(
    data: Mapping[str, Any], membership: TreeMembership
) -> dict[str, Any]:
    """Remove per-tree protected marriage fields from an API response."""
    result = dict(data)
    if not membership.has_access(TreeAccessPermissions.VIEW_MARRIAGE_DATE):
        result["married_at"] = None
    return result
