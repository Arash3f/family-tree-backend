from uuid import UUID

from app.infrastructure.services.unit_of_work.sqlalchemy_uow import SQLAlchemyUnitOfWork


class TreeUnitOfWork(SQLAlchemyUnitOfWork):
    """Unit of Work that also carries the family tree seeded for the current test.

    Genealogy fixtures need a tree to scope persons and marriages to, and nearly
    every test body builds entities with that id. Declaring it here keeps the
    fixtures type-checked instead of attaching the attribute at runtime.
    """

    tree_id: UUID
