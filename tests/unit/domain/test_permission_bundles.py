from app.domain.shared.permissions import Permissions


def test_expand_user_create_includes_user_read_and_role_read():
    expanded = Permissions.expand_with_requirements([Permissions.USER_CREATE])
    assert expanded == {
        Permissions.USER_CREATE,
        Permissions.USER_READ,
        Permissions.ROLE_READ,
    }


def test_expand_role_update_includes_role_read_and_permission_read():
    expanded = Permissions.expand_with_requirements([Permissions.ROLE_UPDATE])
    assert expanded == {
        Permissions.ROLE_UPDATE,
        Permissions.ROLE_READ,
        Permissions.PERMISSION_READ,
    }


def test_genealogy_permissions_are_not_in_system_catalog():
    removed = {
        "person_create",
        "person_read",
        "person_update",
        "person_delete",
        "marriage_create",
        "marriage_read",
        "marriage_update",
        "marriage_delete",
        "marriage_divorce",
        "media_upload",
        "tree_member_add",
        "tree_member_remove",
    }
    assert removed.isdisjoint(Permissions.get_all_permissions())
    assert removed.isdisjoint(Permissions.PERMISSION_REQUIREMENTS)
    assert removed.isdisjoint(Permissions.PERMISSION_DESCRIPTIONS)


def test_expand_ticket_reply():
    expanded = Permissions.expand_with_requirements([Permissions.TICKET_REPLY])
    assert expanded == {Permissions.TICKET_REPLY, Permissions.TICKET_READ}


def test_expand_ticket_create_includes_read_not_reply():
    expanded = Permissions.expand_with_requirements([Permissions.TICKET_CREATE])
    assert expanded == {
        Permissions.TICKET_CREATE,
        Permissions.TICKET_READ,
    }


def test_expand_is_idempotent():
    names = {
        Permissions.USER_CREATE,
        Permissions.USER_READ,
        Permissions.ROLE_READ,
    }
    assert Permissions.expand_with_requirements(names) == names


def test_leaf_permissions_have_no_extra_requirements():
    for leaf in (
        Permissions.USER_READ,
        Permissions.ROLE_READ,
        Permissions.PERMISSION_READ,
        Permissions.TREE_READ,
        Permissions.TICKET_READ,
    ):
        assert Permissions.expand_with_requirements([leaf]) == {leaf}
