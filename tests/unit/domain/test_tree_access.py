from app.domain.shared.tree_access import TreeAccessPermissions


def test_person_update_requires_visibility_needed_by_edit_form():
    assert TreeAccessPermissions.normalize(["person_update"]) == [
        "person_update",
        "view",
        "view_birth_date",
        "view_photo",
    ]


def test_create_permissions_require_view():
    assert TreeAccessPermissions.normalize(["person_create", "marriage_create"]) == [
        "marriage_create",
        "person_create",
        "view",
    ]


def test_full_bundle():
    assert TreeAccessPermissions.normalize(TreeAccessPermissions.ALL) == sorted(
        TreeAccessPermissions.ALL
    )


def test_legacy_coarse_keys_are_unknown():
    assert not TreeAccessPermissions.is_known("edit")
    assert not TreeAccessPermissions.is_known("add_persons")


def test_empty_defaults_to_view():
    assert TreeAccessPermissions.normalize([]) == ["view"]


def test_each_data_visibility_permission_requires_view():
    for permission in (
        TreeAccessPermissions.VIEW_BIRTH_DATE,
        TreeAccessPermissions.VIEW_MARRIAGE_DATE,
        TreeAccessPermissions.VIEW_PHOTO,
    ):
        assert TreeAccessPermissions.normalize([permission]) == ["view", permission]
