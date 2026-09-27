"""Unit tests for kinship path labeling (blood + in-law compression)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.domain.services.relationship_path_label import (
    PathLabels,
    describe_relationship_path,
)


def _ids(n: int) -> list[str]:
    return [str(uuid4()) for _ in range(n)]


def _from_hops(
    hop_specs: list[tuple[str, str | None]],
    *,
    start_gender: str = "MALE",
) -> PathLabels:
    """Build a synthetic path from (kind, reached_gender) hops.

    kind: U / D / S. For U/D, relationship_start_ids are set so that U means
    walking toward the PARENT_OF start node.
    """
    n = len(hop_specs) + 1
    person_ids = _ids(n)
    genders = [start_gender]
    types: list[str] = []
    starts: list[str] = []
    for i, (kind, reached) in enumerate(hop_specs):
        genders.append(reached)
        if kind == "S":
            types.append("SPOUSE_OF")
            starts.append(person_ids[i])  # arbitrary; ignored for spouse
        elif kind == "U":
            types.append("PARENT_OF")
            starts.append(person_ids[i + 1])  # next is the parent (startNode)
        elif kind == "D":
            types.append("PARENT_OF")
            starts.append(person_ids[i])  # current is the parent
        else:
            raise ValueError(kind)
    return describe_relationship_path(person_ids, types, starts, genders)


def test_father_and_mother():
    assert _from_hops([("U", "MALE")]).label_fa == "پدر"
    assert _from_hops([("U", "FEMALE")]).label_en == "mother"


def test_son_daughter_spouse():
    assert _from_hops([("D", "MALE")]).label_fa == "پسر"
    assert _from_hops([("D", "FEMALE")]).label_en == "daughter"
    assert _from_hops([("S", "FEMALE")]).label_fa == "زن"
    assert _from_hops([("S", "MALE")]).label_en == "husband"


def test_sibling():
    labels = _from_hops([("U", "MALE"), ("D", "MALE")])
    assert labels.label_fa == "برادر"
    assert labels.label_en == "brother"
    assert labels.description_fa == "پسرِ پدر"
    assert labels.description_en == "father's son"


def test_grandparents_grandchild():
    assert _from_hops([("U", "MALE"), ("U", "MALE")]).label_fa == "پدربزرگ"
    assert _from_hops([("U", "FEMALE"), ("U", "FEMALE")]).label_en == "grandmother"
    assert _from_hops([("D", "MALE"), ("D", "MALE")]).label_en == "grandson"


def test_paternal_and_maternal_uncles_aunts():
    assert _from_hops([("U", "MALE"), ("U", "MALE"), ("D", "MALE")]).label_fa == "عمو"
    assert _from_hops([("U", "MALE"), ("U", "MALE"), ("D", "FEMALE")]).label_fa == "عمه"
    assert (
        _from_hops([("U", "FEMALE"), ("U", "FEMALE"), ("D", "MALE")]).label_fa == "دایی"
    )
    assert (
        _from_hops([("U", "FEMALE"), ("U", "FEMALE"), ("D", "FEMALE")]).label_fa
        == "خاله"
    )


def test_cousins():
    assert (
        _from_hops(
            [("U", "MALE"), ("U", "MALE"), ("D", "MALE"), ("D", "MALE")]
        ).label_fa
        == "پسرعمو"
    )
    assert (
        _from_hops(
            [("U", "FEMALE"), ("U", "FEMALE"), ("D", "FEMALE"), ("D", "FEMALE")]
        ).label_fa
        == "دخترخاله"
    )
    assert (
        _from_hops(
            [("U", "MALE"), ("U", "MALE"), ("D", "FEMALE"), ("D", "MALE")]
        ).label_en
        == "paternal aunt's son"
    )


def test_niece_nephew_from_origin():
    labels = _from_hops([("U", "MALE"), ("D", "FEMALE"), ("D", "MALE")])
    assert labels.label_fa == "خواهرزاده"
    assert labels.label_en == "nephew"


def test_in_law_layers():
    assert (
        _from_hops(
            [("U", "MALE"), ("U", "MALE"), ("D", "MALE"), ("S", "FEMALE")]
        ).label_fa
        == "زن‌عمو"
    )
    assert (
        _from_hops([("U", "MALE"), ("D", "MALE"), ("S", "FEMALE")]).label_fa
        == "زن‌برادر"
    )
    assert _from_hops([("D", "MALE"), ("S", "FEMALE")]).label_fa == "عروس"
    assert _from_hops([("U", "MALE"), ("S", "FEMALE")]).label_fa == "نامادری"


def test_spouse_parent_and_sibling():
    assert (
        _from_hops([("S", "FEMALE"), ("U", "MALE")], start_gender="MALE").label_fa
        == "پدرزن"
    )
    assert (
        _from_hops([("S", "MALE"), ("U", "FEMALE")], start_gender="FEMALE").label_fa
        == "مادرشوهر"
    )
    assert (
        _from_hops(
            [("S", "FEMALE"), ("U", "FEMALE"), ("D", "MALE")], start_gender="MALE"
        ).label_fa
        == "برادرزن"
    )


@pytest.mark.parametrize(
    "hops",
    [
        # Path 1: via paternal grandfather + wife's mother
        [
            ("U", "MALE"),
            ("U", "MALE"),
            ("D", "MALE"),
            ("S", "FEMALE"),
            ("U", "FEMALE"),
            ("D", "FEMALE"),
            ("D", "MALE"),
        ],
        # Path 2: via paternal grandmother (side still paternal from first U)
        [
            ("U", "MALE"),
            ("U", "FEMALE"),
            ("D", "MALE"),
            ("S", "FEMALE"),
            ("U", "FEMALE"),
            ("D", "FEMALE"),
            ("D", "MALE"),
        ],
        # Path 3: via wife's father
        [
            ("U", "MALE"),
            ("U", "MALE"),
            ("D", "MALE"),
            ("S", "FEMALE"),
            ("U", "MALE"),
            ("D", "FEMALE"),
            ("D", "MALE"),
        ],
    ],
)
def test_three_mehr_arash_to_arash_alipour(hops):
    labels = _from_hops(hops, start_gender="MALE")
    assert labels.label_fa == "پسرِ خواهرِ زن‌عمو"
    assert labels.label_en == "paternal uncle's wife's sister's son"


def test_unknown_gender_fallback():
    labels = _from_hops([("U", None), ("D", None)])
    assert labels.label_fa  # still produces something
    assert "والد" in (labels.description_fa or "") or "فرزند" in (
        labels.description_fa or ""
    )
