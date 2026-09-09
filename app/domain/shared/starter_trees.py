"""Specs for the populated family trees given to every new registrant."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StarterTreeSpec:
    """One starter tree granted on self-signup."""

    key: str
    default_name: str
    template_key: str


# Exactly two trees per new free account — keep in sync with FREE_MAX_OWNED_TREES.
STARTER_TREE_SPECS: tuple[StarterTreeSpec, ...] = (
    StarterTreeSpec(
        key="karimi-en",
        default_name="Karimi Family",
        template_key="karimi-en",
    ),
    StarterTreeSpec(
        key="karimi-fa",
        default_name="خانواده کریمی",
        template_key="karimi-fa",
    ),
)
