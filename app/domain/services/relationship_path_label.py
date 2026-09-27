"""Turn a Neo4j kinship path into Persian / English relationship phrases.

Hop roles come from stored edge direction (PARENT_OF is parent→child) plus
gender. Known segments are compressed left-to-right (longest match first),
including blood terms (عمو، خاله، …) and in-law layers (زن‌عمو، …).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

Gender = Literal["M", "F"] | None
HopKind = Literal["U", "D", "S"]

ZWNJ = "\u200c"
EZ_KASRA = "\u0650"
EZ_HAMZA = "\u0654"
EZ_YE = "ی"


@dataclass(frozen=True, slots=True)
class PathLabels:
    label_fa: str | None
    label_en: str | None
    description_fa: str | None
    description_en: str | None


@dataclass(frozen=True, slots=True)
class _Hop:
    kind: HopKind
    reached: Gender


@dataclass(frozen=True, slots=True)
class _Term:
    fa: str
    en: str


def _norm_gender(value: object) -> Gender:
    if value is None:
        return None
    text = str(value).strip().upper()
    if text in {"M", "MALE"}:
        return "M"
    if text in {"F", "FEMALE"}:
        return "F"
    return None


def _norm_id(value: object) -> str:
    return str(value)


def _with_ezafe(word: str) -> str:
    if not word:
        return word
    last = word[-1]
    if last == "ه":
        return word + EZ_HAMZA
    if last in {"ا", "و"}:
        return word + EZ_YE
    if last == "ی":
        return word + EZ_KASRA
    return word + EZ_KASRA


def _join_fa_words(terms: list[str]) -> str:
    """End-to-start with ezafe: [پدر, پسر] → پسرِ پدر."""
    if not terms:
        return ""
    if len(terms) == 1:
        return terms[0]
    reversed_terms = list(reversed(terms))
    parts = [_with_ezafe(word) for word in reversed_terms[:-1]]
    parts.append(reversed_terms[-1])
    return " ".join(parts)


def _join_en(terms: list[str]) -> str:
    """Start-to-end with 's: [father, son] → father's son."""
    if not terms:
        return ""
    if len(terms) == 1:
        return terms[0]
    return "'s ".join(terms)


def _base_word(hop: _Hop) -> _Term:
    if hop.kind == "U":
        if hop.reached == "M":
            return _Term("پدر", "father")
        if hop.reached == "F":
            return _Term("مادر", "mother")
        return _Term("والد", "parent")
    if hop.kind == "D":
        if hop.reached == "M":
            return _Term("پسر", "son")
        if hop.reached == "F":
            return _Term("دختر", "daughter")
        return _Term("فرزند", "child")
    if hop.reached == "M":
        return _Term("شوهر", "husband")
    if hop.reached == "F":
        return _Term("زن", "wife")
    return _Term("همسر", "spouse")


def _hops_from(
    path_person_ids: list[object],
    relationship_types: list[str],
    relationship_start_ids: list[object],
    genders: list[object],
) -> list[_Hop] | None:
    n = len(path_person_ids)
    if n < 2:
        return None
    if len(relationship_types) != n - 1:
        return None
    if len(relationship_start_ids) != n - 1:
        return None
    if len(genders) != n:
        return None

    hops: list[_Hop] = []
    for i, rel_type in enumerate(relationship_types):
        reached = _norm_gender(genders[i + 1])
        if rel_type == "SPOUSE_OF":
            hops.append(_Hop("S", reached))
            continue
        if rel_type != "PARENT_OF":
            return None
        start = _norm_id(relationship_start_ids[i])
        nxt = _norm_id(path_person_ids[i + 1])
        kind: HopKind = "U" if start == nxt else "D"
        hops.append(_Hop(kind, reached))
    return hops


def _uncle_aunt(side: Gender, dest: Gender) -> _Term | None:
    if side == "M":
        if dest == "M":
            return _Term("عمو", "paternal uncle")
        if dest == "F":
            return _Term("عمه", "paternal aunt")
    elif side == "F":
        if dest == "M":
            return _Term("دایی", "maternal uncle")
        if dest == "F":
            return _Term("خاله", "maternal aunt")
    return None


def _cousin(side: Gender, mid: Gender, final: Gender) -> _Term | None:
    stem = _uncle_aunt(side, mid)
    if stem is None or final is None:
        return None
    if final == "M":
        return _Term(f"پسر{stem.fa}", f"{stem.en}'s son")
    return _Term(f"دختر{stem.fa}", f"{stem.en}'s daughter")


def _match_blood(
    hops: list[_Hop], i: int, *, allow_niece_nephew: bool
) -> tuple[_Term, int] | None:
    """Longest blood pattern at hop i. Returns (term, hop_count)."""
    remaining = len(hops) - i
    if remaining <= 0:
        return None

    if (
        remaining >= 4
        and hops[i].kind == "U"
        and hops[i + 1].kind == "U"
        and hops[i + 2].kind == "D"
        and hops[i + 3].kind == "D"
    ):
        cousin = _cousin(hops[i].reached, hops[i + 2].reached, hops[i + 3].reached)
        if cousin is not None:
            return cousin, 4

    if (
        remaining >= 3
        and hops[i].kind == "U"
        and hops[i + 1].kind == "U"
        and hops[i + 2].kind == "D"
    ):
        uncle = _uncle_aunt(hops[i].reached, hops[i + 2].reached)
        if uncle is not None:
            return uncle, 3

    # برادرزاده / خواهرزاده only as the whole relation from the origin, so
    # nested paths keep «پسرِ خواهرِ …» instead of «خواهرزادهِ …».
    if (
        allow_niece_nephew
        and remaining >= 3
        and hops[i].kind == "U"
        and hops[i + 1].kind == "D"
        and hops[i + 2].kind == "D"
    ):
        sibling = hops[i + 1].reached
        child = hops[i + 2].reached
        en = "nephew" if child == "M" else "niece" if child == "F" else "nibling"
        if sibling == "M":
            return _Term("برادرزاده", en), 3
        if sibling == "F":
            return _Term("خواهرزاده", en), 3

    if remaining >= 2 and hops[i].kind == "U" and hops[i + 1].kind == "U":
        dest = hops[i + 1].reached
        if dest == "M":
            return _Term("پدربزرگ", "grandfather"), 2
        if dest == "F":
            return _Term("مادربزرگ", "grandmother"), 2

    if remaining >= 2 and hops[i].kind == "D" and hops[i + 1].kind == "D":
        dest = hops[i + 1].reached
        if dest == "M":
            return _Term("نوه", "grandson"), 2
        if dest == "F":
            return _Term("نوه", "granddaughter"), 2
        return _Term("نوه", "grandchild"), 2

    if remaining >= 2 and hops[i].kind == "U" and hops[i + 1].kind == "D":
        dest = hops[i + 1].reached
        if dest == "M":
            return _Term("برادر", "brother"), 2
        if dest == "F":
            return _Term("خواهر", "sister"), 2

    return _base_word(hops[i]), 1


def _in_law_after(term: _Term, spouse_hop: _Hop) -> _Term | None:
    if spouse_hop.kind != "S":
        return None
    mapping = {
        "عمو": _Term(f"زن{ZWNJ}عمو", "paternal uncle's wife"),
        "عمه": _Term("شوهرعمه", "paternal aunt's husband"),
        "دایی": _Term(f"زن{ZWNJ}دایی", "maternal uncle's wife"),
        "خاله": _Term("شوهرخاله", "maternal aunt's husband"),
        "برادر": _Term(f"زن{ZWNJ}برادر", "sister-in-law"),
        "خواهر": _Term("شوهرخواهر", "brother-in-law"),
        "پسر": _Term("عروس", "daughter-in-law"),
        "دختر": _Term("داماد", "son-in-law"),
        "پدر": _Term("نامادری", "stepmother"),
        "مادر": _Term("ناپدری", "stepfather"),
    }
    return mapping.get(term.fa)


def _spouse_parent(owner: Gender, parent: Gender) -> _Term:
    if owner == "M":
        if parent == "M":
            return _Term("پدرزن", "father-in-law")
        if parent == "F":
            return _Term("مادرزن", "mother-in-law")
    elif owner == "F":
        if parent == "M":
            return _Term("پدرشوهر", "father-in-law")
        if parent == "F":
            return _Term("مادرشوهر", "mother-in-law")
    spouse = _base_word(_Hop("S", None))
    parent_t = _base_word(_Hop("U", parent))
    return _Term(
        _join_fa_words([spouse.fa, parent_t.fa]),
        _join_en([spouse.en, parent_t.en]),
    )


def _spouse_sibling(owner: Gender, sibling: Gender) -> _Term:
    if owner == "M":
        if sibling == "M":
            return _Term("برادرزن", "brother-in-law")
        if sibling == "F":
            return _Term("خواهرزن", "sister-in-law")
    elif owner == "F":
        if sibling == "M":
            return _Term("برادرشوهر", "brother-in-law")
        if sibling == "F":
            return _Term(f"خواهر{ZWNJ}شوهر", "sister-in-law")
    spouse = _base_word(_Hop("S", None))
    sib = (
        _Term("برادر", "brother")
        if sibling == "M"
        else _Term("خواهر", "sister")
        if sibling == "F"
        else _Term("خواهر/برادر", "sibling")
    )
    return _Term(
        _join_fa_words([spouse.fa, sib.fa]),
        _join_en([spouse.en, sib.en]),
    )


def _compress(hops: list[_Hop], owner_genders: list[Gender]) -> list[_Term]:
    terms: list[_Term] = []
    i = 0
    n = len(hops)
    while i < n:
        if (
            i + 2 < n
            and hops[i].kind == "S"
            and hops[i + 1].kind == "U"
            and hops[i + 2].kind == "D"
        ):
            terms.append(_spouse_sibling(owner_genders[i], hops[i + 2].reached))
            i += 3
            continue
        if i + 1 < n and hops[i].kind == "S" and hops[i + 1].kind == "U":
            terms.append(_spouse_parent(owner_genders[i], hops[i + 1].reached))
            i += 2
            continue

        matched = _match_blood(hops, i, allow_niece_nephew=(i == 0))
        assert matched is not None
        term, length = matched
        next_i = i + length
        if next_i < n and hops[next_i].kind == "S":
            layered = _in_law_after(term, hops[next_i])
            if layered is not None:
                terms.append(layered)
                i = next_i + 1
                continue
        terms.append(term)
        i = next_i
    return terms


def describe_relationship_path(
    path_person_ids: list[object] | tuple[object, ...],
    relationship_types: list[str] | tuple[str, ...],
    relationship_start_ids: list[object] | tuple[object, ...],
    genders: list[object] | tuple[object, ...],
) -> PathLabels:
    ids = list(path_person_ids)
    types = list(relationship_types)
    starts = list(relationship_start_ids)
    gens = list(genders)
    hops = _hops_from(ids, types, starts, gens)
    if not hops:
        return PathLabels(None, None, None, None)

    base_terms = [_base_word(hop) for hop in hops]
    description_fa = _join_fa_words([t.fa for t in base_terms])
    description_en = _join_en([t.en for t in base_terms])

    owner_genders = [_norm_gender(gens[i]) for i in range(len(hops))]
    compressed = _compress(hops, owner_genders)
    label_fa = _join_fa_words([t.fa for t in compressed])
    label_en = _join_en([t.en for t in compressed])

    return PathLabels(
        label_fa=label_fa or None,
        label_en=label_en or None,
        description_fa=description_fa or None,
        description_en=description_en or None,
    )


def labels_for_row(
    *,
    person_ids: list[UUID] | tuple[UUID, ...],
    relationship_types: list[str] | tuple[str, ...],
    relationship_start_ids: list[object] | tuple[object, ...] | None,
    genders: list[object] | tuple[object, ...] | None,
) -> PathLabels:
    if not relationship_start_ids or not genders:
        return PathLabels(None, None, None, None)
    return describe_relationship_path(
        list(person_ids),
        list(relationship_types),
        list(relationship_start_ids),
        list(genders),
    )
