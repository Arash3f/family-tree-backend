from typing import LiteralString

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

SHORTEST_RELATIONSHIP_PATH: LiteralString = """
MATCH (a:Person {id: $from_id}), (b:Person {id: $to_id})
WHERE ($tree_id IS NULL OR (a.tree_id = $tree_id AND b.tree_id = $tree_id))
OPTIONAL MATCH path = shortestPath((a)-[*..15]-(b))
RETURN
  CASE WHEN path IS NULL THEN [] ELSE [n IN nodes(path) | n.id] END AS person_ids,
  CASE WHEN path IS NULL THEN [] ELSE [r IN relationships(path) | type(r)] END
    AS relationship_types,
  CASE WHEN path IS NULL THEN NULL ELSE length(path) END AS distance
"""
