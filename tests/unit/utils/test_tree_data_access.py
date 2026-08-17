from datetime import date
from uuid import uuid4

from app.domain.entities.family_tree import TreeMemberRole, TreeMembership
from app.domain.shared.tree_access import TreeAccessPermissions
from app.presentation.tree_data_access import (
    redact_marriage_data,
    redact_person_data,
)


def membership_with(*permissions: str) -> TreeMembership:
    return TreeMembership(
        id=uuid4(),
        tree_id=uuid4(),
        user_id=uuid4(),
        role=TreeMemberRole.MEMBER,
        permissions=list(permissions),
    )


def test_person_redaction_hides_birth_date_and_both_photo_fields():
    membership = membership_with(TreeAccessPermissions.VIEW)
    result = redact_person_data(
        {
            "name": "Ali",
            "birth_date": date(2000, 1, 1),
            "photo_object_key": "people/photo.webp",
            "photo_url": "/media/people/photo.webp",
        },
        membership,
    )

    assert result["birth_date"] is None
    assert result["photo_object_key"] is None
    assert result["photo_url"] is None


def test_person_redaction_preserves_granted_fields():
    membership = membership_with(
        TreeAccessPermissions.VIEW_BIRTH_DATE,
        TreeAccessPermissions.VIEW_PHOTO,
    )
    data = {
        "birth_date": date(2000, 1, 1),
        "photo_object_key": "people/photo.webp",
        "photo_url": "/media/people/photo.webp",
    }

    assert redact_person_data(data, membership) == data


def test_marriage_redaction_hides_married_at():
    membership = membership_with(TreeAccessPermissions.VIEW)

    assert (
        redact_marriage_data({"married_at": date(2020, 1, 1)}, membership)["married_at"]
        is None
    )
