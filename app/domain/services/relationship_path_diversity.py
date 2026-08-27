from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

MAX_DIVERSE_PATHS = 4
MAX_PATH_HOPS = 15
LENGTH_SLACK = 8
MAX_INTERMEDIATE_JACCARD = 0.35
K_SHORTEST_POOL = 20


@dataclass(frozen=True)
class PathRecord:
    person_ids: tuple[UUID, ...]
    relationship_types: tuple[str, ...]
    distance: int


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
    max_hops: int = MAX_PATH_HOPS,
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
