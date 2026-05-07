import pytest
from sqlalchemy.exc import IntegrityError

from app.infrastructure.database.models import PersonModel


@pytest.mark.asyncio
async def test_unique_constraint_same_name_and_parents(uow):
    async with uow:
        father = PersonModel(name="Ali", gender="male")
        mother = PersonModel(name="Sara", gender="female")

        uow.session.add_all([father, mother])
        await uow.session.flush()

        child1 = PersonModel(
            name="Reza",
            gender="male",
            father_id=father.id,
            mother_id=mother.id,
        )

        uow.session.add(child1)
        await uow.session.flush()

        child2 = PersonModel(
            name="Reza",
            gender="male",
            father_id=father.id,
            mother_id=mother.id,
        )

        uow.session.add(child2)

        with pytest.raises(IntegrityError):
            await uow.session.flush()
