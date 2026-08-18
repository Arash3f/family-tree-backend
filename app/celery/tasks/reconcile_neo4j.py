import asyncio
import logging
import uuid
from contextlib import contextmanager, suppress
from datetime import UTC, datetime
from uuid import UUID

import redis
from celery import shared_task

from app.core.config import settings
from app.domain.entities.marriage import Marriage
from app.domain.entities.person import Person
from app.domain.shared.dto.family_tree_dto import PersonUpsertDTO
from app.infrastructure.database.neo4j import neo4j_queries as q
from app.infrastructure.database.neo4j.neo4j import neo4j_client
from app.infrastructure.database.session import async_session
from app.infrastructure.repositories.marriage_repository_sql import (
    SQLMarriageRepository,
)
from app.infrastructure.repositories.person_repository_sql import SQLPersonRepository
from app.infrastructure.repositories.tree_repository_sql import SQLTreeRepository

logger = logging.getLogger(__name__)

_LOCK_KEY = "reconcile_neo4j:lock"
# Comfortably longer than the hourly beat interval, so a run that's still
# legitimately in progress at the next scheduled tick doesn't get its lock
# reaped out from under it by a stale-lock cleanup elsewhere.
_LOCK_TTL_SECONDS = 90 * 60


@contextmanager
def _reconciliation_lock():
    """Best-effort mutex so overlapping beat-scheduled runs don't double-process
    the same trees (see M9-adjacent risk noted during review: no distributed
    lock previously existed, and a run exceeding the hourly beat interval
    would otherwise start a second, overlapping run against the same data).

    Redis unavailability fails open (yields True) rather than blocking the
    whole reconciliation job on a lock service outage -- worst case under
    that condition is the pre-existing double-run risk, not a stuck job.
    """
    token = str(uuid.uuid4())
    client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
    acquired = False
    try:
        try:
            acquired = bool(client.set(_LOCK_KEY, token, nx=True, ex=_LOCK_TTL_SECONDS))
        except redis.RedisError:
            logger.warning(
                "Could not reach Redis for the reconciliation lock; "
                "proceeding without it."
            )
            acquired = True
        yield acquired
    finally:
        if acquired:
            with suppress(redis.RedisError):
                if client.get(_LOCK_KEY) == token.encode():
                    client.delete(_LOCK_KEY)
        with suppress(redis.RedisError):
            client.close()


async def _load_postgres_state(
    tree_id: UUID,
) -> tuple[list[Person], list[Marriage]]:
    async with async_session() as session:
        persons = await SQLPersonRepository(session).get_by_tree_id(tree_id)
        marriages = await SQLMarriageRepository(session).get_by_tree_id(tree_id)
        return persons, marriages


async def _list_tree_ids() -> list[UUID]:
    async with async_session() as session:
        trees = await SQLTreeRepository(session).list_all()
        return [tree.safe_id for tree in trees]


def _person_payload(person: Person) -> dict:
    return {
        "id": str(person.safe_id),
        "full_name": person.name,
        "gender": person.gender.value.upper(),
        "birth_date": person.birth_date.isoformat() if person.birth_date else None,
        "death_date": person.death_date.isoformat() if person.death_date else None,
        "tree_id": str(person.tree_id),
    }


async def _reconcile_tree(
    tree_id: UUID, persons: list[Person], marriages: list[Marriage]
) -> dict:
    """Diff Postgres state for one tree against Neo4j and repair drift.

    Runs outside the request path (no real-time outbox exists yet, see H5 in
    REVIEW.md) so this is what catches nodes/relationships silently dropped
    by a crash between Postgres commit and Celery enqueue, or by
    CREATE_SPOUSE_REL/CREATE_PARENT_REL no-oping when a node was missing.
    """
    repaired = {"persons": 0, "parent_rels": 0, "spouse_rels": 0}
    now_utc = datetime.now(UTC)

    existing_ids = {
        UUID(str(row["id"]))
        for row in await neo4j_client.execute_read(
            q.LIST_PERSON_IDS_IN_TREE, params={"tree_id": str(tree_id)}
        )
    }

    persons_by_id = {person.safe_id: person for person in persons}
    for person in persons:
        if person.safe_id not in existing_ids:
            payload = _person_payload(person)
            payload["created_at"] = now_utc.isoformat()
            payload["updated_at"] = now_utc.isoformat()
            await neo4j_client.execute_write(
                q.UPSERT_PERSON, params=PersonUpsertDTO.model_validate(payload)
            )
            repaired["persons"] += 1
            logger.warning(
                "Reconciliation: recreated missing Neo4j person node %s (tree=%s)",
                person.safe_id,
                tree_id,
            )

    expected_parent_pairs = {
        (parent_id, person.safe_id)
        for person in persons
        for parent_id in person.parent_ids
        if parent_id in persons_by_id
    }
    existing_parent_pairs = {
        (UUID(str(row["parent_id"])), UUID(str(row["child_id"])))
        for row in await neo4j_client.execute_read(
            q.LIST_PARENT_PAIRS_IN_TREE, params={"tree_id": str(tree_id)}
        )
    }
    for parent_id, child_id in expected_parent_pairs - existing_parent_pairs:
        await neo4j_client.execute_write(
            q.CREATE_PARENT_REL,
            params={"parent_id": str(parent_id), "child_id": str(child_id)},
        )
        repaired["parent_rels"] += 1
        logger.warning(
            "Reconciliation: recreated missing PARENT_OF %s -> %s (tree=%s)",
            parent_id,
            child_id,
            tree_id,
        )

    expected_spouse_pairs = {
        tuple(sorted((marriage.spouse_a_id, marriage.spouse_b_id), key=str))
        for marriage in marriages
        if marriage.divorced_at is None
    }
    existing_spouse_pairs = {
        tuple(
            sorted(
                (UUID(str(row["person_id_1"])), UUID(str(row["person_id_2"]))), key=str
            )
        )
        for row in await neo4j_client.execute_read(
            q.LIST_SPOUSE_PAIRS_IN_TREE, params={"tree_id": str(tree_id)}
        )
    }
    for person_id_1, person_id_2 in expected_spouse_pairs - existing_spouse_pairs:
        await neo4j_client.execute_write(
            q.CREATE_SPOUSE_REL,
            params={"person_id_1": str(person_id_1), "person_id_2": str(person_id_2)},
        )
        repaired["spouse_rels"] += 1
        logger.warning(
            "Reconciliation: recreated missing SPOUSE_OF %s <-> %s (tree=%s)",
            person_id_1,
            person_id_2,
            tree_id,
        )

    return repaired


@shared_task(
    name="reconcile.neo4j",
    bind=True,
    max_retries=3,
    retry_backoff=True,
    autoretry_for=(ConnectionError, TimeoutError, RuntimeError),
)
def reconcile_neo4j(self):
    """Detect and repair Postgres -> Neo4j sync drift across all trees.

    Best-effort safety net, not a substitute for a transactional outbox:
    it heals missing nodes/relationships but cannot detect stale data left
    behind by a Neo4j delete that never ran.
    """
    with _reconciliation_lock() as acquired:
        if not acquired:
            logger.info(
                "Skipping this reconciliation run: a previous run is still in progress."
            )
            return {"skipped": "already running"}

        tree_ids = asyncio.run(_list_tree_ids())
        totals = {"persons": 0, "parent_rels": 0, "spouse_rels": 0}
        trees_with_drift = 0

        async def _reconcile_one_tree(tree_id: UUID) -> dict:
            persons, marriages = await _load_postgres_state(tree_id)
            return await _reconcile_tree(tree_id, persons, marriages)

        for tree_id in tree_ids:
            repaired = asyncio.run(_reconcile_one_tree(tree_id))
            if any(repaired.values()):
                trees_with_drift += 1
            for key, value in repaired.items():
                totals[key] += value

        if trees_with_drift:
            logger.error(
                "Neo4j reconciliation repaired drift in %s tree(s): %s",
                trees_with_drift,
                totals,
            )
        else:
            logger.info(
                "Neo4j reconciliation: no drift found across %s tree(s)",
                len(tree_ids),
            )

        return {
            "trees_checked": len(tree_ids),
            "trees_with_drift": trees_with_drift,
            **totals,
        }
