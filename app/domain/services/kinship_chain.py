"""Name a relation spelled out as a chain of family steps ("father's brother's son").

The public kinship tool lets anyone build such a chain without a tree. Each
step is turned into the hops a real path in the graph would have, and the
result goes through the same labeller the product uses for paths between two
people, so the tool can never name a relation differently from the app.
"""

from collections.abc import Sequence
from enum import StrEnum

from app.domain.services.relationship_path_label import (
    PathLabels,
    describe_relationship_path,
)

MAX_KINSHIP_STEPS = 8


class KinshipStep(StrEnum):
    FATHER = "father"
    MOTHER = "mother"
    SON = "son"
    DAUGHTER = "daughter"
    BROTHER = "brother"
    SISTER = "sister"
    HUSBAND = "husband"
    WIFE = "wife"


_UP, _DOWN, _SPOUSE = "U", "D", "S"

# Each step as graph hops: (direction, gender of the person reached). A sibling
# is not an edge in the graph — it is up to a parent and down again, and which
# parent does not change the name.
_STEP_HOPS: dict[KinshipStep, tuple[tuple[str, str | None], ...]] = {
    KinshipStep.FATHER: ((_UP, "M"),),
    KinshipStep.MOTHER: ((_UP, "F"),),
    KinshipStep.SON: ((_DOWN, "M"),),
    KinshipStep.DAUGHTER: ((_DOWN, "F"),),
    KinshipStep.BROTHER: ((_UP, None), (_DOWN, "M")),
    KinshipStep.SISTER: ((_UP, None), (_DOWN, "F")),
    KinshipStep.HUSBAND: ((_SPOUSE, "M"),),
    KinshipStep.WIFE: ((_SPOUSE, "F"),),
}

# In-law names depend on whose spouse it is (پدرزن vs پدرشوهر). Mid-chain the
# previous step says who that is; for the first step only "my wife" or "my
# husband" reveals the speaker's own gender.
_SPEAKER_GENDER = {KinshipStep.WIFE: "M", KinshipStep.HUSBAND: "F"}


def label_kinship_chain(steps: Sequence[KinshipStep]) -> PathLabels:
    """
    Name the relation reached by walking `steps` from the speaker.

    Args:
        steps: The chain from the speaker outwards, e.g. ``[FATHER, BROTHER,
            SON]`` for "my father's brother's son"; 1 to ``MAX_KINSHIP_STEPS``.

    Returns:
        PathLabels: The Persian and English names (``label_fa`` / ``label_en``)
        and the literal hop-by-hop descriptions.

    Raises:
        ValueError: When the chain is empty or longer than ``MAX_KINSHIP_STEPS``.
    """
    if not 1 <= len(steps) <= MAX_KINSHIP_STEPS:
        raise ValueError(f"a chain has 1 to {MAX_KINSHIP_STEPS} steps")

    # Synthetic people 0..n stand in for the nodes of a real path. Typed as the
    # labeller takes them, since it accepts any id and gender representation.
    person_ids: list[object] = [0]
    genders: list[object] = [_SPEAKER_GENDER.get(steps[0])]
    relationship_types: list[str] = []
    relationship_start_ids: list[object] = []

    for step in steps:
        for direction, gender in _STEP_HOPS[step]:
            current, reached = len(person_ids) - 1, len(person_ids)
            person_ids.append(reached)
            genders.append(gender)
            if direction == _SPOUSE:
                relationship_types.append("SPOUSE_OF")
                relationship_start_ids.append(current)
            else:
                # PARENT_OF runs parent -> child, so going up starts at the
                # person reached and going down starts where we stand.
                relationship_types.append("PARENT_OF")
                relationship_start_ids.append(reached if direction == _UP else current)

    return describe_relationship_path(
        person_ids, relationship_types, relationship_start_ids, genders
    )
