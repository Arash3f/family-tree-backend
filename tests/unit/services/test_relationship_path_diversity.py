from uuid import UUID, uuid4

from app.domain.services.relationship_path_diversity import (
    PathRecord,
    select_diverse_paths,
)


def _path(*names: str, distance: int | None = None) -> PathRecord:
    ids = tuple(UUID(int=ord(name)) for name in names)
    rels = tuple(["PARENT_OF"] * (len(ids) - 1))
    return PathRecord(
        person_ids=ids,
        relationship_types=rels,
        distance=distance if distance is not None else len(ids) - 1,
    )


def test_diamond_keeps_both_parent_routes():
    shortest = _path("A", "F", "C")
    other = _path("A", "M", "C")

    selected = select_diverse_paths(shortest, [other])

    assert selected == [shortest, other]


def test_near_duplicate_father_mother_swap_is_rejected():
    shortest = _path("A", "F", "G", "U", "B")
    via_mother = _path("A", "M", "G", "U", "B")

    selected = select_diverse_paths(shortest, [via_mother])

    assert selected == [shortest]


def test_shared_ancestor_keeps_a_path_that_still_differs():
    shortest = _path("A", "G", "P", "Q", "B")
    via_other_branch = _path("A", "G", "X", "Y", "B")

    selected = select_diverse_paths(shortest, [via_other_branch])

    assert selected == [shortest, via_other_branch]


def test_longer_duplicate_identity_is_ignored():
    shortest = _path("A", "B")
    same = _path("A", "B")

    selected = select_diverse_paths(shortest, [same])

    assert selected == [shortest]


def test_paths_beyond_length_slack_are_dropped():
    shortest = _path("A", "B")
    too_long_ids = tuple(uuid4() for _ in range(12))
    too_long = PathRecord(
        person_ids=(shortest.person_ids[0], *too_long_ids, shortest.person_ids[-1]),
        relationship_types=tuple(["PARENT_OF"] * 13),
        distance=13,
    )

    selected = select_diverse_paths(shortest, [too_long], length_slack=8)

    assert selected == [shortest]


def test_greedy_prefers_least_overlap_over_shorter_near_copy():
    shortest = _path("A", "P", "Q", "B")
    near = _path("A", "P", "R", "B")
    disjoint = _path("A", "X", "Y", "Z", "B")

    selected = select_diverse_paths(shortest, [near, disjoint])

    assert selected[0] == shortest
    assert disjoint in selected
    assert near not in selected
