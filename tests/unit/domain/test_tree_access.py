from app.domain.shared.tree_access import TreeAccessPermissions


def test_edit_requires_view():
    assert TreeAccessPermissions.normalize(["edit"]) == ["edit", "view"]


def test_add_persons_requires_view():
    assert TreeAccessPermissions.normalize(["add_persons"]) == [
        "add_persons",
        "view",
    ]


def test_full_bundle():
    assert TreeAccessPermissions.normalize(["edit", "add_persons"]) == [
        "add_persons",
        "edit",
        "view",
    ]


def test_empty_defaults_to_view():
    assert TreeAccessPermissions.normalize([]) == ["view"]
