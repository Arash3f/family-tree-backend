from collections.abc import Sequence
from dataclasses import dataclass
from math import log10
from uuid import UUID

MAX_DIVERSE_PATHS = 3
# Soft default when tree size is unknown; prefer path_hops_for_tree_size().
DEFAULT_PATH_HOPS = 10
MIN_PATH_HOPS = 8
MAX_PATH_HOPS_CAP = 24
LENGTH_SLACK = 4
MAX_INTERMEDIATE_JACCARD = 0.35
K_SHORTEST_POOL = 6
# Only run the expensive k-shortest fallback when avoiding did not yield
# at least one route distinct from the shortest.
MIN_PATHS_BEFORE_K_SHORTEST = 2

# Keep for callers/tests that still import the old name as "ceiling for selection".
MAX_PATH_HOPS = MAX_PATH_HOPS_CAP


@dataclass(frozen=True)
class PathRecord:
    person_ids: tuple[UUID, ...]
    relationship_types: tuple[str, ...]
    distance: int


def path_hops_for_tree_size(person_count: int) -> int:
    """Scale Neo4j path depth with how many people are in the tree.

    Kinship diameters grow slowly with population (extra generations, not
    linearly with n). ``6 + 4·log10(n)`` stays near 10 for small trees and
    climbs toward the safety cap for very large pedigrees:

    - ~10 people → 10 hops
    - ~100 people → 14 hops
    - ~1_000 people → 18 hops
    - ~10_000 people → 22 hops (capped at 24)
    """
    n = max(0, int(person_count))
    if n <= 1:
        return MIN_PATH_HOPS
    raw = 6.0 + 4.0 * log10(n)
    return int(min(MAX_PATH_HOPS_CAP, max(MIN_PATH_HOPS, round(raw))))


def clamp_path_hops(max_hops: int) -> int:
    return int(min(MAX_PATH_HOPS_CAP, max(MIN_PATH_HOPS, int(max_hops))))


def intermediate_ids(path: PathRecord) -> frozenset[UUID]:
    if len(path.person_ids) <= 2:
        return frozenset()
    return frozenset(path.person_ids[1:-1])


def jaccard(left: frozenset[UUID], right: frozenset[UUID]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 1.0
    return len(left & right) / len(union)


def too_similar(
    left: frozenset[UUID],
    right: frozenset[UUID],
    max_jaccard: float = MAX_INTERMEDIATE_JACCARD,
) -> bool:
    """True when two paths would look the same to a person reading the tree."""
    if jaccard(left, right) > max_jaccard:
        return True
    # Father vs mother of the same couple: one-node swap, rest shared.
    return bool(left and right and len(left ^ right) <= 2 and (left & right))


def path_identity(path: PathRecord) -> tuple[UUID, ...]:
    return path.person_ids


def select_diverse_paths(
    shortest: PathRecord,
    candidates: Sequence[PathRecord],
    *,
    k: int = MAX_DIVERSE_PATHS,
    max_jaccard: float = MAX_INTERMEDIATE_JACCARD,
    length_slack: int = LENGTH_SLACK,
    max_hops: int = DEFAULT_PATH_HOPS,
) -> list[PathRecord]:
    """Keep the shortest path, then greedily add paths with the least overlap.

    Later paths are not required to be short — they must look different. Near
    duplicates (high Jaccard, or a single swapped intermediate) are dropped.
    """
    selected = [shortest]
    seen = {path_identity(shortest), tuple(reversed(shortest.person_ids))}
    max_length = min(max_hops, shortest.distance + length_slack)

    remaining: list[PathRecord] = []
    for candidate in candidates:
        identity = path_identity(candidate)
        if identity in seen:
            continue
        if candidate.distance > max_length:
            continue
        remaining.append(candidate)

    while len(selected) < k and remaining:
        best_index: int | None = None
        best_score: tuple[float, int] | None = None
        for index, candidate in enumerate(remaining):
            intermediates = intermediate_ids(candidate)
            if any(
                too_similar(intermediates, intermediate_ids(chosen), max_jaccard)
                for chosen in selected
            ):
                continue
            max_similarity = max(
                jaccard(intermediates, intermediate_ids(chosen)) for chosen in selected
            )
            score = (1.0 - max_similarity, -candidate.distance)
            if best_score is None or score > best_score:
                best_score = score
                best_index = index

        if best_index is None:
            break
        chosen = remaining.pop(best_index)
        selected.append(chosen)
        seen.add(path_identity(chosen))
        seen.add(tuple(reversed(chosen.person_ids)))

    return selected
