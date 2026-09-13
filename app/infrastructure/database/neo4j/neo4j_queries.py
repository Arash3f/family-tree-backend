from typing import LiteralString, cast

CONSTRAINT_PERSON_ID: LiteralString = """
CREATE CONSTRAINT person_id_unique IF NOT EXISTS
FOR (p:Person)
REQUIRE p.id IS UNIQUE
"""

# ============================
# PERSON
# ============================

UPSERT_PERSON: LiteralString = """
MERGE (p:Person {id: $id})
SET p.full_name  = $full_name,
    p.gender     = $gender,
    p.birth_date = $birth_date,
    p.death_date = $death_date,
    p.tree_id    = $tree_id,
    p.created_at = coalesce(p.created_at, $created_at),
    p.updated_at = $updated_at
RETURN p
"""

DELETE_PERSON: LiteralString = """
MATCH (p:Person {id: $id})
DETACH DELETE p
RETURN COUNT(p) > 0 AS deleted
"""

GET_PERSON: LiteralString = """
MATCH (p:Person {id: $id})
RETURN p
"""

PERSON_EXISTS: LiteralString = """
MATCH (p:Person {id: $id})
WHERE $tree_id IS NULL OR p.tree_id = $tree_id
RETURN p LIMIT 1
"""

LIST_PERSON_IDS_IN_TREE: LiteralString = """
MATCH (p:Person {tree_id: $tree_id})
RETURN p.id AS id
"""

LIST_SPOUSE_PAIRS_IN_TREE: LiteralString = """
MATCH (a:Person {tree_id: $tree_id})-[:SPOUSE_OF]-(b:Person {tree_id: $tree_id})
WHERE a.id < b.id
RETURN a.id AS person_id_1, b.id AS person_id_2
"""

LIST_PARENT_PAIRS_IN_TREE: LiteralString = """
MATCH (p:Person {tree_id: $tree_id})-[:PARENT_OF]->(c:Person {tree_id: $tree_id})
RETURN p.id AS parent_id, c.id AS child_id
"""

COUNT_PERSONS_IN_TREE: LiteralString = """
MATCH (p:Person {tree_id: $tree_id})
RETURN count(p) AS n
"""

# ============================
# RELATIONSHIPS
# ============================

CREATE_PARENT_REL: LiteralString = """
MATCH (parent:Person {id: $parent_id})
MATCH (child:Person {id: $child_id})
MERGE (parent)-[:PARENT_OF]->(child)
RETURN parent, child
"""

DELETE_PARENT_REL: LiteralString = """
MATCH (p:Person {id: $parent_id})-[r:PARENT_OF]->(c:Person {id: $child_id})
DELETE r
RETURN COUNT(r) > 0 AS deleted
"""

CREATE_SPOUSE_REL: LiteralString = """
MATCH (a:Person {id: $person_id_1})
MATCH (b:Person {id: $person_id_2})
MERGE (a)-[:SPOUSE_OF]-(b)
RETURN a, b
"""

DELETE_SPOUSE_REL: LiteralString = """
MATCH (a:Person {id: $person_id_1})-[r:SPOUSE_OF]-(b:Person {id: $person_id_2})
DELETE r
RETURN COUNT(r) > 0 AS deleted
"""


def _clamp_hops(max_hops: int) -> int:
    # Local clamp so this module does not import domain (keeps infra leaf-ish).
    return int(min(24, max(8, int(max_hops))))


def _hop_filter(*, avoiding: bool = False, male_only: bool = False) -> str:
    """Quantified-path hop WHERE clause (tree scope + optional filters)."""
    parts = ["($tree_id IS NULL OR (x.tree_id = $tree_id AND y.tree_id = $tree_id))"]
    if avoiding:
        parts.append("NOT y.id IN $excluded_ids")
    if male_only:
        # Endpoints may be any gender; every intermediate hop target must be male.
        parts.append("(y = b OR y.gender = 'MALE')")
    return " AND\n      ".join(parts)


def shortest_relationship_path_query(
    max_hops: int, *, male_only: bool = False
) -> LiteralString:
    """Shortest kinship path; hop bound is size-scaled by the caller."""
    hops = _clamp_hops(max_hops)
    hop_where = _hop_filter(male_only=male_only)
    return cast(
        LiteralString,
        (
            "MATCH (a:Person {id: $from_id}), (b:Person {id: $to_id})\n"
            "WHERE ($tree_id IS NULL OR "
            "(a.tree_id = $tree_id AND b.tree_id = $tree_id))\n"
            "MATCH path = SHORTEST 1 PATHS\n"
            "  (a)((x)-[:PARENT_OF|SPOUSE_OF]-(y)\n"
            f"    WHERE {hop_where}\n"
            f"  ){{1,{hops}}}(b)\n"
            "RETURN\n"
            "  [n IN nodes(path) | n.id] AS person_ids,\n"
            "  [r IN relationships(path) | type(r)] AS relationship_types,\n"
            "  length(path) AS distance\n"
        ),
    )


def shortest_relationship_path_avoiding_query(
    max_hops: int, *, male_only: bool = False
) -> LiteralString:
    """Next shortest path that skips already-used intermediate people."""
    hops = _clamp_hops(max_hops)
    hop_where = _hop_filter(avoiding=True, male_only=male_only)
    return cast(
        LiteralString,
        (
            "MATCH (a:Person {id: $from_id}), (b:Person {id: $to_id})\n"
            "WHERE ($tree_id IS NULL OR "
            "(a.tree_id = $tree_id AND b.tree_id = $tree_id))\n"
            "MATCH path = SHORTEST 1 PATHS\n"
            "  (a)((x)-[:PARENT_OF|SPOUSE_OF]-(y)\n"
            f"    WHERE {hop_where}\n"
            f"  ){{1,{hops}}}(b)\n"
            "RETURN\n"
            "  [n IN nodes(path) | n.id] AS person_ids,\n"
            "  [r IN relationships(path) | type(r)] AS relationship_types,\n"
            "  length(path) AS distance\n"
        ),
    )


def k_shortest_relationship_paths_query(
    max_hops: int, *, pool: int = 6, male_only: bool = False
) -> LiteralString:
    """Bounded k-shortest fallback when avoiding cannot diversify."""
    hops = _clamp_hops(max_hops)
    k = int(min(20, max(1, int(pool))))
    hop_where = _hop_filter(male_only=male_only)
    return cast(
        LiteralString,
        (
            "MATCH (a:Person {id: $from_id}), (b:Person {id: $to_id})\n"
            "WHERE ($tree_id IS NULL OR "
            "(a.tree_id = $tree_id AND b.tree_id = $tree_id))\n"
            f"MATCH path = SHORTEST {k} PATHS\n"
            "  (a)((x)-[:PARENT_OF|SPOUSE_OF]-(y)\n"
            f"    WHERE {hop_where}\n"
            f"  ){{1,{hops}}}(b)\n"
            "RETURN\n"
            "  [n IN nodes(path) | n.id] AS person_ids,\n"
            "  [rel IN relationships(path) | type(rel)] AS relationship_types,\n"
            "  length(path) AS distance\n"
        ),
    )


# Backward-compatible aliases for the previous fixed-bound queries (default 10).
SHORTEST_RELATIONSHIP_PATH: LiteralString = shortest_relationship_path_query(10)
SHORTEST_RELATIONSHIP_PATH_AVOIDING: LiteralString = (
    shortest_relationship_path_avoiding_query(10)
)
K_SHORTEST_RELATIONSHIP_PATHS: LiteralString = k_shortest_relationship_paths_query(10)
