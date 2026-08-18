from datetime import UTC, date

import pytest
from sqlalchemy.exc import IntegrityError

from app.infrastructure.database.models import (
    MarriageModel,
    ParentLinkModel,
    PersonModel,
)


@pytest.mark.asyncio
async def test_unique_constraint_same_name_under_same_marriage(uow):
    husband = PersonModel(tree_id=uow.tree_id, name="Ali", gender="male")
    wife = PersonModel(tree_id=uow.tree_id, name="Sara", gender="female")
    uow.session.add_all([husband, wife])
    await uow.session.flush()

    marriage = MarriageModel(
        tree_id=uow.tree_id,
        spouse_a_id=husband.id,
        spouse_b_id=wife.id,
        married_at=date(2000, 1, 1),
    )
    uow.session.add(marriage)
    await uow.session.flush()

    child1 = PersonModel(
        tree_id=uow.tree_id, name="Reza", gender="male", marriage_id=marriage.id
    )
    uow.session.add(child1)
    await uow.session.flush()

    child2 = PersonModel(
        tree_id=uow.tree_id, name="Reza", gender="male", marriage_id=marriage.id
    )
    uow.session.add(child2)

    with pytest.raises(IntegrityError):
        await uow.session.flush()


@pytest.mark.asyncio
async def test_same_name_without_marriage_is_allowed(uow):
    uow.session.add_all(
        [
            PersonModel(tree_id=uow.tree_id, name="Reza", gender="male"),
            PersonModel(tree_id=uow.tree_id, name="Reza", gender="male"),
        ]
    )
    await uow.session.flush()


@pytest.mark.asyncio
async def test_parent_link_rejects_self_parent(uow):
    person = PersonModel(tree_id=uow.tree_id, name="Reza", gender="male")
    uow.session.add(person)
    await uow.session.flush()

    uow.session.add(
        ParentLinkModel(
            child_id=person.id,
            parent_id=person.id,
            relationship_type="biological",
        )
    )

    with pytest.raises(IntegrityError):
        await uow.session.flush()


@pytest.mark.asyncio
async def test_parent_link_rejects_cycle(uow):
    parent = PersonModel(tree_id=uow.tree_id, name="Ali", gender="male")
    child = PersonModel(tree_id=uow.tree_id, name="Reza", gender="male")
    uow.session.add_all([parent, child])
    await uow.session.flush()

    uow.session.add(
        ParentLinkModel(
            child_id=child.id,
            parent_id=parent.id,
            relationship_type="biological",
        )
    )
    await uow.session.flush()

    uow.session.add(
        ParentLinkModel(
            child_id=parent.id,
            parent_id=child.id,
            relationship_type="biological",
        )
    )

    with pytest.raises(IntegrityError):
        await uow.session.flush()


@pytest.mark.asyncio
async def test_parent_link_rejects_third_biological_parent(uow):
    p1 = PersonModel(tree_id=uow.tree_id, name="P1", gender="male")
    p2 = PersonModel(tree_id=uow.tree_id, name="P2", gender="female")
    p3 = PersonModel(tree_id=uow.tree_id, name="P3", gender="male")
    child = PersonModel(tree_id=uow.tree_id, name="Child", gender="male")
    uow.session.add_all([p1, p2, p3, child])
    await uow.session.flush()

    uow.session.add_all(
        [
            ParentLinkModel(
                child_id=child.id,
                parent_id=p1.id,
                relationship_type="biological",
            ),
            ParentLinkModel(
                child_id=child.id,
                parent_id=p2.id,
                relationship_type="biological",
            ),
        ]
    )
    await uow.session.flush()

    uow.session.add(
        ParentLinkModel(
            child_id=child.id,
            parent_id=p3.id,
            relationship_type="biological",
        )
    )

    with pytest.raises(IntegrityError):
        await uow.session.flush()


@pytest.mark.asyncio
async def test_adoptive_parent_beyond_two_biological_is_allowed(uow):
    p1 = PersonModel(tree_id=uow.tree_id, name="P1", gender="male")
    p2 = PersonModel(tree_id=uow.tree_id, name="P2", gender="female")
    p3 = PersonModel(tree_id=uow.tree_id, name="P3", gender="male")
    child = PersonModel(tree_id=uow.tree_id, name="Child", gender="male")
    uow.session.add_all([p1, p2, p3, child])
    await uow.session.flush()

    uow.session.add_all(
        [
            ParentLinkModel(
                child_id=child.id,
                parent_id=p1.id,
                relationship_type="biological",
            ),
            ParentLinkModel(
                child_id=child.id,
                parent_id=p2.id,
                relationship_type="biological",
            ),
            ParentLinkModel(
                child_id=child.id,
                parent_id=p3.id,
                relationship_type="adoptive",
            ),
        ]
    )
    await uow.session.flush()


@pytest.mark.asyncio
async def test_same_gender_marriage_is_allowed(uow):
    spouse_a = PersonModel(tree_id=uow.tree_id, name="Alex", gender="male")
    spouse_b = PersonModel(tree_id=uow.tree_id, name="Sam", gender="male")
    uow.session.add_all([spouse_a, spouse_b])
    await uow.session.flush()

    uow.session.add(
        MarriageModel(
            tree_id=uow.tree_id,
            spouse_a_id=spouse_a.id,
            spouse_b_id=spouse_b.id,
            married_at=date(2020, 1, 1),
        )
    )
    await uow.session.flush()


@pytest.mark.asyncio
async def test_multiple_active_marriages_for_same_person_allowed(uow):
    spouse_a = PersonModel(tree_id=uow.tree_id, name="Ali", gender="male")
    spouse_b = PersonModel(tree_id=uow.tree_id, name="Sara", gender="female")
    spouse_c = PersonModel(tree_id=uow.tree_id, name="Maryam", gender="female")
    uow.session.add_all([spouse_a, spouse_b, spouse_c])
    await uow.session.flush()

    uow.session.add_all(
        [
            MarriageModel(
                tree_id=uow.tree_id,
                spouse_a_id=spouse_a.id,
                spouse_b_id=spouse_b.id,
                married_at=date(2010, 1, 1),
            ),
            MarriageModel(
                tree_id=uow.tree_id,
                spouse_a_id=spouse_a.id,
                spouse_b_id=spouse_c.id,
                married_at=date(2015, 1, 1),
            ),
        ]
    )
    await uow.session.flush()


@pytest.mark.asyncio
async def test_divorce_before_marriage_rejected(uow):
    spouse_a = PersonModel(tree_id=uow.tree_id, name="Ali", gender="male")
    spouse_b = PersonModel(tree_id=uow.tree_id, name="Sara", gender="female")
    uow.session.add_all([spouse_a, spouse_b])
    await uow.session.flush()

    uow.session.add(
        MarriageModel(
            tree_id=uow.tree_id,
            spouse_a_id=spouse_a.id,
            spouse_b_id=spouse_b.id,
            married_at=date(2020, 1, 1),
            divorced_at=date(2019, 1, 1),
        )
    )

    with pytest.raises(IntegrityError):
        await uow.session.flush()


@pytest.mark.asyncio
async def test_soft_deleted_person_frees_name_under_marriage(uow):
    from datetime import datetime

    spouse_a = PersonModel(tree_id=uow.tree_id, name="Ali", gender="male")
    spouse_b = PersonModel(tree_id=uow.tree_id, name="Sara", gender="female")
    uow.session.add_all([spouse_a, spouse_b])
    await uow.session.flush()

    marriage = MarriageModel(
        tree_id=uow.tree_id,
        spouse_a_id=spouse_a.id,
        spouse_b_id=spouse_b.id,
        married_at=date(2000, 1, 1),
    )
    uow.session.add(marriage)
    await uow.session.flush()

    child = PersonModel(
        tree_id=uow.tree_id,
        name="Reza",
        gender="male",
        marriage_id=marriage.id,
    )
    uow.session.add(child)
    await uow.session.flush()

    child.deleted_at = datetime.now(UTC)
    await uow.session.flush()

    replacement = PersonModel(
        tree_id=uow.tree_id,
        name="Reza",
        gender="male",
        marriage_id=marriage.id,
    )
    uow.session.add(replacement)
    await uow.session.flush()
