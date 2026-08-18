"""Optional family-tree sample data.

Copy this file to ``seed_items.py`` (gitignored), then enable the call in
``app/main.py`` lifespan:

    from seed_items import seed_initial_items
    await seed_initial_items(uow=uow)

Seed order matches the current domain model:
1. Root people (no parents / no origin marriage)
2. Marriages between existing people
3. Children with ``marriage_id`` = origin marriage and biological parents
   matching that marriage's spouses
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import NotRequired, TypedDict
from uuid import UUID

from app.application.interfaces.unit_of_work import UnitOfWork
from app.core.config import settings
from app.domain.entities.family_tree import FamilyTree, TreeMemberRole, TreeMembership
from app.domain.entities.marriage import Marriage
from app.domain.entities.person import (
    Gender,
    ParentLink,
    ParentRelationshipType,
    Person,
)
from app.domain.exceptions.person_exceptions import InvalidParentMarriageException
from app.domain.shared.dto.family_tree_dto import (
    ParentRelationshipDTO,
    PersonUpsertDTO,
    SpouseRelationshipDTO,
)
from app.infrastructure.repositories.neo4j_family_tree_repository import (
    Neo4jFamilyTreeRepository,
)


class ParentSeedLink(TypedDict):
    key: str
    relationship_type: NotRequired[ParentRelationshipType]


class PersonSeedData(TypedDict):
    key: str
    name: str
    gender: Gender
    family_name: NotRequired[str | None]
    birth_date: NotRequired[date | None]
    death_date: NotRequired[date | None]
    birth_place: NotRequired[str | None]
    death_place: NotRequired[str | None]
    notes: NotRequired[str | None]
    parents: NotRequired[list[ParentSeedLink]]
    # Key from SEED_MARRIAGES — the marriage this person was born into.
    origin_marriage: NotRequired[str]


class MarriageSeedData(TypedDict):
    key: str
    spouse_a: str
    spouse_b: str
    married_at: date
    divorced_at: NotRequired[date | None]


SAMPLE_TREE_NAME = "سمپل خانواده"


async def get_or_create_sample_tree(uow: UnitOfWork) -> FamilyTree:
    admin = await uow.users.get_by_username(settings.ADMIN_USERNAME)
    if not admin:
        raise RuntimeError(
            f"Admin user {settings.ADMIN_USERNAME!r} not found; "
            "run seed_initial_user first"
        )

    for tree in await uow.family_trees.list_for_user(admin.safe_id):
        if tree.name == SAMPLE_TREE_NAME:
            membership = await uow.tree_memberships.get(
                tree_id=tree.safe_id, user_id=admin.safe_id
            )
            if not membership:
                await uow.tree_memberships.create(
                    TreeMembership(
                        id=None,
                        tree_id=tree.safe_id,
                        user_id=admin.safe_id,
                        role=TreeMemberRole.OWNER,
                    )
                )
                await uow.commit()
            return tree

    tree = await uow.family_trees.create(
        FamilyTree(
            id=None,
            name=SAMPLE_TREE_NAME,
            owner_user_id=admin.safe_id,
        )
    )
    await uow.tree_memberships.create(
        TreeMembership(
            id=None,
            tree_id=tree.safe_id,
            user_id=admin.safe_id,
            role=TreeMemberRole.OWNER,
        )
    )
    await uow.commit()
    return tree


async def get_or_create_person(
    uow: UnitOfWork,
    person: Person,
    neo_repo: Neo4jFamilyTreeRepository,
    *,
    tree_id: UUID,
) -> Person:
    now_utc = datetime.now(UTC)
    created_at: datetime | None = None

    find_person = await uow.persons.get_by_name(
        name=person.name, marriage_id=person.marriage_id, tree_id=tree_id
    )

    if find_person:
        person.id = find_person.safe_id
        person = await uow.persons.update(person=person)
    else:
        person = await uow.persons.create(person=person)
        created_at = now_utc

    await neo_repo.upsert_person(
        PersonUpsertDTO(
            id=person.safe_id,
            tree_id=tree_id,
            full_name=person.name,
            gender=person.gender.value.upper(),
            birth_date=person.birth_date,
            death_date=person.death_date,
            created_at=created_at,
            updated_at=now_utc,
        )
    )

    for parent_id in person.parent_ids:
        await neo_repo.create_parent_relationship(
            ParentRelationshipDTO(
                child_id=person.safe_id,
                parent_id=parent_id,
            )
        )

    await uow.commit()
    return person


async def get_or_create_marriage(
    uow: UnitOfWork,
    marriage: Marriage,
    neo_repo: Neo4jFamilyTreeRepository,
    *,
    tree_id: UUID,
) -> Marriage:
    find_marriage = await uow.marriages.get_by_ids(
        spouse_a_id=marriage.spouse_a_id,
        spouse_b_id=marriage.spouse_b_id,
    )

    if find_marriage:
        marriage.id = find_marriage.id
        marriage = await uow.marriages.update(marriage=marriage)
    else:
        marriage = await uow.marriages.create(marriage=marriage)

    await neo_repo.create_spouse_relationship(
        SpouseRelationshipDTO(
            person_id_1=marriage.spouse_a_id,
            person_id_2=marriage.spouse_b_id,
        )
    )

    await uow.commit()
    return marriage


def _build_parents(
    item: PersonSeedData, people_map: dict[str, Person]
) -> list[ParentLink]:
    parents: list[ParentLink] = []
    for link in item.get("parents", []):
        parents.append(
            ParentLink(
                parent_id=people_map[link["key"]].safe_id,
                relationship_type=link.get(
                    "relationship_type", ParentRelationshipType.BIOLOGICAL
                ),
            )
        )
    return parents


def _validate_origin_marriage_parents(
    *,
    parents: list[ParentLink],
    marriage: Marriage,
) -> None:
    spouse_ids = {marriage.spouse_a_id, marriage.spouse_b_id}
    for link in parents:
        if (
            link.relationship_type is ParentRelationshipType.BIOLOGICAL
            and link.parent_id not in spouse_ids
        ):
            raise InvalidParentMarriageException()


# ---------------------------------------------------------------------------
# Sample family (2 generations)
#
#   حسن الفونه ──spouse── مریم کریمی
#           └── آرش الفونه
#
#   پرویز ابراهیمی ──spouse── ناهید رضایی
#           └── رز ابراهیمی
#
#   آرش الفونه ──spouse── رز ابراهیمی
#           ├── مانی الفونه   (biological)
#           ├── سارا الفونه   (biological)
#           └── کیان موسوی    (adoptive; same origin marriage)
# ---------------------------------------------------------------------------

SEED_PEOPLE: list[PersonSeedData] = [
    # Generation 0 — roots
    {
        "key": "hasan_alfooneh",
        "name": "حسن",
        "family_name": "الفونه",
        "gender": Gender.MALE,
        "birth_date": date(1932, 3, 12),
        "birth_place": "تهران",
    },
    {
        "key": "maryam_karimi",
        "name": "مریم",
        "family_name": "کریمی",
        "gender": Gender.FEMALE,
        "birth_date": date(1938, 7, 21),
        "birth_place": "اصفهان",
    },
    {
        "key": "parviz_ebrahimi",
        "name": "پرویز",
        "family_name": "ابراهیمی",
        "gender": Gender.MALE,
        "birth_date": date(1928, 11, 5),
        "birth_place": "شیراز",
    },
    {
        "key": "nahid_rezaei",
        "name": "ناهید",
        "family_name": "رضایی",
        "gender": Gender.FEMALE,
        "birth_date": date(1935, 1, 30),
        "birth_place": "تبریز",
    },
    # Generation 1 — children of root marriages
    {
        "key": "arash_alfooneh",
        "name": "آرش",
        "family_name": "الفونه",
        "gender": Gender.MALE,
        "birth_date": date(1964, 5, 14),
        "birth_place": "تهران",
        "origin_marriage": "hasan_maryam",
        "parents": [
            {"key": "hasan_alfooneh"},
            {"key": "maryam_karimi"},
        ],
    },
    {
        "key": "roz_ebrahimi",
        "name": "رز",
        "family_name": "ابراهیمی",
        "gender": Gender.FEMALE,
        "birth_date": date(1971, 9, 2),
        "birth_place": "شیراز",
        "origin_marriage": "parviz_nahid",
        "parents": [
            {"key": "parviz_ebrahimi"},
            {"key": "nahid_rezaei"},
        ],
    },
    # Generation 2 — children of آرش + رز
    {
        "key": "mani_alfooneh",
        "name": "مانی",
        "family_name": "الفونه",
        "gender": Gender.MALE,
        "birth_date": date(1996, 4, 18),
        "birth_place": "تهران",
        "origin_marriage": "arash_roz",
        "parents": [
            {"key": "arash_alfooneh"},
            {"key": "roz_ebrahimi"},
        ],
    },
    {
        "key": "sara_alfooneh",
        "name": "سارا",
        "family_name": "الفونه",
        "gender": Gender.FEMALE,
        "birth_date": date(2004, 12, 1),
        "birth_place": "تهران",
        "origin_marriage": "arash_roz",
        "parents": [
            {"key": "arash_alfooneh"},
            {"key": "roz_ebrahimi"},
        ],
    },
    {
        "key": "kian_mousavi",
        "name": "کیان",
        "family_name": "موسوی",
        "gender": Gender.MALE,
        "birth_date": date(2013, 6, 9),
        "birth_place": "کرج",
        "notes": "فرزندخوانده خانواده آرش و رز",
        "origin_marriage": "arash_roz",
        "parents": [
            {
                "key": "arash_alfooneh",
                "relationship_type": ParentRelationshipType.ADOPTIVE,
            },
            {
                "key": "roz_ebrahimi",
                "relationship_type": ParentRelationshipType.ADOPTIVE,
            },
        ],
    },
]

SEED_MARRIAGES: list[MarriageSeedData] = [
    {
        "key": "hasan_maryam",
        "spouse_a": "hasan_alfooneh",
        "spouse_b": "maryam_karimi",
        "married_at": date(1960, 6, 1),
    },
    {
        "key": "parviz_nahid",
        "spouse_a": "parviz_ebrahimi",
        "spouse_b": "nahid_rezaei",
        "married_at": date(1962, 8, 20),
    },
    {
        "key": "arash_roz",
        "spouse_a": "arash_alfooneh",
        "spouse_b": "roz_ebrahimi",
        "married_at": date(1994, 1, 1),
    },
]


def _can_seed_person(
    item: PersonSeedData,
    people_map: dict[str, Person],
    marriages_map: dict[str, Marriage],
) -> bool:
    if item["key"] in people_map:
        return False

    for link in item.get("parents", []):
        if link["key"] not in people_map:
            return False

    origin_key = item.get("origin_marriage")
    return not (origin_key is not None and origin_key not in marriages_map)


def _can_seed_marriage(
    item: MarriageSeedData,
    people_map: dict[str, Person],
    marriages_map: dict[str, Marriage],
) -> bool:
    if item["key"] in marriages_map:
        return False
    return item["spouse_a"] in people_map and item["spouse_b"] in people_map


async def seed_initial_items(uow: UnitOfWork) -> FamilyTree:
    people_map: dict[str, Person] = {}
    marriages_map: dict[str, Marriage] = {}
    neo_repo = Neo4jFamilyTreeRepository()

    async with uow:
        tree = await get_or_create_sample_tree(uow)
        tree_id = tree.safe_id

        # Multi-pass: roots → marriages → children → next-gen marriages → …
        while True:
            progressed = False

            for marriage_item in SEED_MARRIAGES:
                if not _can_seed_marriage(marriage_item, people_map, marriages_map):
                    continue

                marriage = await get_or_create_marriage(
                    uow=uow,
                    marriage=Marriage(
                        id=None,
                        tree_id=tree_id,
                        spouse_a_id=people_map[marriage_item["spouse_a"]].safe_id,
                        spouse_b_id=people_map[marriage_item["spouse_b"]].safe_id,
                        married_at=marriage_item["married_at"],
                        divorced_at=marriage_item.get("divorced_at"),
                    ),
                    neo_repo=neo_repo,
                    tree_id=tree_id,
                )
                marriages_map[marriage_item["key"]] = marriage
                progressed = True

            for person_item in SEED_PEOPLE:
                if not _can_seed_person(person_item, people_map, marriages_map):
                    continue

                parents = _build_parents(person_item, people_map)
                origin_key = person_item.get("origin_marriage")
                marriage_id: UUID | None = None

                if origin_key is not None:
                    origin_marriage = marriages_map[origin_key]
                    _validate_origin_marriage_parents(
                        parents=parents, marriage=origin_marriage
                    )
                    marriage_id = origin_marriage.safe_id

                person = await get_or_create_person(
                    uow=uow,
                    person=Person(
                        id=None,
                        tree_id=tree_id,
                        name=person_item["name"],
                        gender=person_item["gender"],
                        family_name=person_item.get("family_name"),
                        birth_date=person_item.get("birth_date"),
                        death_date=person_item.get("death_date"),
                        birth_place=person_item.get("birth_place"),
                        death_place=person_item.get("death_place"),
                        notes=person_item.get("notes"),
                        parents=parents,
                        marriage_id=marriage_id,
                    ),
                    neo_repo=neo_repo,
                    tree_id=tree_id,
                )
                people_map[person_item["key"]] = person
                progressed = True

            if not progressed:
                break

        missing_people = [p["key"] for p in SEED_PEOPLE if p["key"] not in people_map]
        missing_marriages = [
            m["key"] for m in SEED_MARRIAGES if m["key"] not in marriages_map
        ]
        if missing_people or missing_marriages:
            raise RuntimeError(
                "Seed graph has unresolved dependencies: "
                f"people={missing_people}, marriages={missing_marriages}"
            )

        return tree
