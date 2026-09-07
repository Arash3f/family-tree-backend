"""Specs for the empty family trees given to every new registrant.

Populate `template_key` later (persons/marriages) without changing call sites —
`StarterTreeProvisioner` already iterates these definitions.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StarterTreeSpec:
    """One starter tree granted on self-signup."""

    key: str
    default_name: str
    # Reserved for a future seed/template loader (Excel, fixtures, Neo4j, …).
    template_key: str | None = None


# Exactly two trees per new free account — keep in sync with FREE_MAX_OWNED_TREES.
STARTER_TREE_SPECS: tuple[StarterTreeSpec, ...] = (
    StarterTreeSpec(
        key="personal",
        default_name="My Family Tree",
        template_key=None,
    ),
    StarterTreeSpec(
        key="sample",
        default_name="Sample Family Tree",
        template_key=None,
    ),
)
