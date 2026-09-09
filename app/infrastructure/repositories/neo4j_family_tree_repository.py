from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.repositories.family_tree_repository import FamilyTreeRepository
from app.domain.services.relationship_path_diversity import (
    DEFAULT_PATH_HOPS,
    K_SHORTEST_POOL,
    MAX_DIVERSE_PATHS,
    MIN_PATHS_BEFORE_K_SHORTEST,
    PathRecord,
    clamp_path_hops,
    path_hops_for_tree_size,
    select_diverse_paths,
)
from app.domain.shared.dto.family_tree_dto import (
    DeleteRelationshipDTO,
    DeleteSpouseRelationshipDTO,
    ParentRelationshipDTO,
    ParentRelationshipResponseDTO,
    PersonIdDTO,
    PersonResponseDTO,
    PersonUpsertDTO,
    RelationshipPathDTO,
    RelationshipPathItemDTO,
    SpouseRelationshipDTO,
    SpouseRelationshipResponseDTO,
)
from app.infrastructure.database.neo4j import neo4j_queries as q
from app.infrastructure.database.neo4j.neo4j import neo4j_client
from app.infrastructure.utils.mapper.parent_mapper import map_neo4j_parent
from app.infrastructure.utils.mapper.person_mapper import map_neo4j_person
from app.infrastructure.utils.mapper.spouse_mapper import map_neo4j_spouse


class _PathParams(BaseModel):
    from_id: UUID
    to_id: UUID
    tree_id: UUID | None = None


class _PathAvoidParams(BaseModel):
    from_id: UUID
    to_id: UUID
    tree_id: UUID | None = None
    excluded_ids: list[UUID] = Field(default_factory=list)


class _PersonExistsParams(BaseModel):
    id: UUID
    tree_id: UUID | None = None


class Neo4jFamilyTreeRepository(FamilyTreeRepository):
    # ============================
    # PERSON
    # ============================

    async def upsert_person(self, data: PersonUpsertDTO) -> PersonResponseDTO:
        records = await neo4j_client.execute_write(query=q.UPSERT_PERSON, params=data)

        return map_neo4j_person(records[0])

    async def delete_person(self, data: PersonIdDTO) -> bool:
        records = await neo4j_client.execute_write(query=q.DELETE_PERSON, params=data)
        if not records:
            return False

        return bool(records[0]["deleted"])

    async def get_person(self, data: PersonIdDTO) -> PersonResponseDTO:
        result = await neo4j_client.execute_read(query=q.GET_PERSON, params=data)
        return map_neo4j_person(result[0])

    async def person_exists(
        self, data: PersonIdDTO, tree_id: UUID | None = None
    ) -> bool:
        result = await neo4j_client.execute_read(
            query=q.PERSON_EXISTS,
            params=_PersonExistsParams(
                id=data.id, tree_id=tree_id if tree_id is not None else data.tree_id
            ),
        )
        return len(result) > 0

    # ============================
    # RELATIONSHIPS
    # ============================

    async def create_parent_relationship(
        self, data: ParentRelationshipDTO
    ) -> ParentRelationshipResponseDTO:
        records = await neo4j_client.execute_write(
            query=q.CREATE_PARENT_REL,
            params=data,
        )
        if not records:
            # Same race as create_spouse_relationship: CREATE_PARENT_REL
            # MATCHes both nodes, so a missing one silently drops the edge
            # unless we raise here to trigger the caller's retry.
            raise RuntimeError(
                f"Cannot create parent relationship: person node(s) not found "
                f"for parent={data.parent_id} and/or child={data.child_id}"
            )
        return map_neo4j_parent(records[0])

    async def delete_parent_relationship(self, data: DeleteRelationshipDTO) -> bool:
        records = await neo4j_client.execute_write(
            query=q.DELETE_PARENT_REL,
            params=data,
        )

        if not records:
            return False

        return bool(records[0]["deleted"])

    async def create_spouse_relationship(
        self, data: SpouseRelationshipDTO
    ) -> SpouseRelationshipResponseDTO:
        records = await neo4j_client.execute_write(
            query=q.CREATE_SPOUSE_REL,
            params=data,
        )
        if not records:
            # CREATE_SPOUSE_REL MATCHes both Person nodes; an empty result
            # means one hasn't been synced yet. Raise so the caller's retry
            # (celery autoretry_for=RuntimeError) can heal the race instead
            # of silently dropping the relationship.
            raise RuntimeError(
                f"Cannot create spouse relationship: person node(s) not found "
                f"for {data.person_id_1} and/or {data.person_id_2}"
            )
        return map_neo4j_spouse(records[0])

    async def delete_spouse_relationship(
        self, data: DeleteSpouseRelationshipDTO
    ) -> bool:
        records = await neo4j_client.execute_write(
            query=q.DELETE_SPOUSE_REL,
            params=data,
        )

        if not records:
            return False

        return bool(records[0]["deleted"])

    async def find_shortest_relationship_path(
        self,
        from_person_id: UUID,
        to_person_id: UUID,
        tree_id: UUID | None = None,
        *,
        max_hops: int | None = None,
        person_count: int | None = None,
    ) -> RelationshipPathDTO:
        hops = await self._resolve_max_hops(
            tree_id, max_hops=max_hops, person_count=person_count
        )
        records = await neo4j_client.execute_read(
            query=q.shortest_relationship_path_query(hops),
            params=_PathParams(
                from_id=from_person_id, to_id=to_person_id, tree_id=tree_id
            ),
        )

        if not records:
            return RelationshipPathDTO(
                from_person_id=from_person_id,
                to_person_id=to_person_id,
                found=False,
            )

        row = records[0]
        distance = row.get("distance")
        person_ids = [UUID(str(pid)) for pid in (row.get("person_ids") or [])]
        relationship_types = list(row.get("relationship_types") or [])
        found = distance is not None and len(person_ids) >= 2

        paths = (
            [
                RelationshipPathItemDTO(
                    distance=int(distance),
                    path_person_ids=person_ids,
                    relationship_types=relationship_types,
                )
            ]
            if found
            else []
        )

        return RelationshipPathDTO(
            from_person_id=from_person_id,
            to_person_id=to_person_id,
            found=found,
            distance=distance if found else None,
            path_person_ids=person_ids if found else [],
            relationship_types=relationship_types if found else [],
            paths=paths,
        )

    async def find_diverse_relationship_paths(
        self,
        from_person_id: UUID,
        to_person_id: UUID,
        tree_id: UUID | None = None,
        *,
        max_hops: int | None = None,
        person_count: int | None = None,
    ) -> RelationshipPathDTO:
        hops = await self._resolve_max_hops(
            tree_id, max_hops=max_hops, person_count=person_count
        )
        shortest = await self.find_shortest_relationship_path(
            from_person_id,
            to_person_id,
            tree_id=tree_id,
            max_hops=hops,
        )
        if not shortest.found or shortest.distance is None:
            return shortest

        shortest_record = _dto_to_record(shortest)
        candidates: list[PathRecord] = []
        excluded = list(shortest.path_person_ids[1:-1])

        if excluded:
            for _ in range(MAX_DIVERSE_PATHS - 1):
                avoided = await self._shortest_path_avoiding(
                    from_person_id, to_person_id, tree_id, excluded, hops
                )
                if avoided is None:
                    break
                candidates.append(avoided)
                excluded.extend(avoided.person_ids[1:-1])

        # k-shortest is a fallback only when avoiding failed to produce another
        # distinct route (e.g. marriage edge with a via-child alternative).
        if (
            1 + _unique_candidate_count(shortest_record, candidates)
            < MIN_PATHS_BEFORE_K_SHORTEST
        ):
            candidates.extend(
                await self._k_shortest_paths(
                    from_person_id, to_person_id, tree_id, hops
                )
            )

        selected = select_diverse_paths(shortest_record, candidates, max_hops=hops)
        return _records_to_dto(from_person_id, to_person_id, selected)

    async def _resolve_max_hops(
        self,
        tree_id: UUID | None,
        *,
        max_hops: int | None,
        person_count: int | None,
    ) -> int:
        if max_hops is not None:
            return clamp_path_hops(max_hops)
        if person_count is not None:
            return path_hops_for_tree_size(person_count)
        if tree_id is not None:
            return path_hops_for_tree_size(await self._count_persons_in_tree(tree_id))
        return DEFAULT_PATH_HOPS

    async def _count_persons_in_tree(self, tree_id: UUID) -> int:
        records = await neo4j_client.execute_read(
            query=q.COUNT_PERSONS_IN_TREE,
            params={"tree_id": str(tree_id)},
        )
        if not records:
            return 0
        return int(records[0].get("n") or 0)

    async def _shortest_path_avoiding(
        self,
        from_person_id: UUID,
        to_person_id: UUID,
        tree_id: UUID | None,
        excluded_ids: list[UUID],
        max_hops: int,
    ) -> PathRecord | None:
        records = await neo4j_client.execute_read(
            query=q.shortest_relationship_path_avoiding_query(max_hops),
            params=_PathAvoidParams(
                from_id=from_person_id,
                to_id=to_person_id,
                tree_id=tree_id,
                excluded_ids=excluded_ids,
            ),
        )
        if not records:
            return None
        return _row_to_record(records[0])

    async def _k_shortest_paths(
        self,
        from_person_id: UUID,
        to_person_id: UUID,
        tree_id: UUID | None,
        max_hops: int,
    ) -> list[PathRecord]:
        records = await neo4j_client.execute_read(
            query=q.k_shortest_relationship_paths_query(max_hops, pool=K_SHORTEST_POOL),
            params=_PathParams(
                from_id=from_person_id, to_id=to_person_id, tree_id=tree_id
            ),
        )
        paths: list[PathRecord] = []
        for row in records:
            record = _row_to_record(row)
            if record is not None:
                paths.append(record)
        return paths


def _row_to_record(row: dict) -> PathRecord | None:
    distance = row.get("distance")
    person_ids = [UUID(str(pid)) for pid in (row.get("person_ids") or [])]
    if distance is None or len(person_ids) < 2:
        return None
    return PathRecord(
        person_ids=tuple(person_ids),
        relationship_types=tuple(row.get("relationship_types") or []),
        distance=int(distance),
    )


def _dto_to_record(path: RelationshipPathDTO) -> PathRecord:
    return PathRecord(
        person_ids=tuple(path.path_person_ids),
        relationship_types=tuple(path.relationship_types),
        distance=path.distance or 0,
    )


def _unique_candidate_count(shortest: PathRecord, candidates: list[PathRecord]) -> int:
    seen = {shortest.person_ids}
    unique = 0
    for candidate in candidates:
        if candidate.person_ids in seen:
            continue
        seen.add(candidate.person_ids)
        unique += 1
    return unique


def _records_to_dto(
    from_person_id: UUID,
    to_person_id: UUID,
    selected: list[PathRecord],
) -> RelationshipPathDTO:
    if not selected:
        return RelationshipPathDTO(
            from_person_id=from_person_id,
            to_person_id=to_person_id,
            found=False,
        )
    first = selected[0]
    return RelationshipPathDTO(
        from_person_id=from_person_id,
        to_person_id=to_person_id,
        found=True,
        distance=first.distance,
        path_person_ids=list(first.person_ids),
        relationship_types=list(first.relationship_types),
        paths=[
            RelationshipPathItemDTO(
                distance=path.distance,
                path_person_ids=list(path.person_ids),
                relationship_types=list(path.relationship_types),
            )
            for path in selected
        ],
    )
