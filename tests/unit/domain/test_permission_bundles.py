from app.domain.shared.permissions import Permissions


def test_expand_user_create_includes_user_read_and_role_read():
    expanded = Permissions.expand_with_requirements([Permissions.USER_CREATE])
    assert expanded == {
        Permissions.USER_CREATE,
        Permissions.USER_READ,
        Permissions.ROLE_READ,
    }


def test_expand_person_create_includes_person_read_and_tree_read():
    expanded = Permissions.expand_with_requirements([Permissions.PERSON_CREATE])
    assert expanded == {
        Permissions.PERSON_CREATE,
        Permissions.PERSON_READ,
        Permissions.TREE_READ,
    }


def test_expand_marriage_create_is_transitive():
    expanded = Permissions.expand_with_requirements([Permissions.MARRIAGE_CREATE])
    assert expanded == {
        Permissions.MARRIAGE_CREATE,
        Permissions.MARRIAGE_READ,
        Permissions.PERSON_READ,
        Permissions.TREE_READ,
    }


def test_expand_role_update_includes_role_read_and_permission_read():
    expanded = Permissions.expand_with_requirements([Permissions.ROLE_UPDATE])
    assert expanded == {
        Permissions.ROLE_UPDATE,
        Permissions.ROLE_READ,
        Permissions.PERMISSION_READ,
    }


def test_expand_tree_member_add():
    expanded = Permissions.expand_with_requirements([Permissions.TREE_MEMBER_ADD])
    assert expanded == {
        Permissions.TREE_MEMBER_ADD,
        Permissions.TREE_READ,
        Permissions.USER_READ,
    }


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
