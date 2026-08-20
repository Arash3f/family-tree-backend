"""Guards against the migrations and the ORM models drifting apart.

Tests build their schema with ``Base.metadata.create_all`` while production
runs ``alembic upgrade head``. Nothing otherwise notices when a model gains a
column, an index or a constraint that no migration creates, and the mismatch
only surfaces in production.
"""

from argparse import Namespace

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext

from app.core.config import settings
from app.infrastructure.database.base import Base

SCRATCH_DB = f"{settings.POSTGRES_DB_TEST}_migration_check"

# Alembic's own bookkeeping table is never part of the model metadata.
IGNORED_TABLES = {"alembic_version"}

EXPECTED_TRIGGERS = {
    "trg_parent_link_rules",
    "trg_person_marriage_parent_rules",
}


def _sync_url(database: str) -> str:
    return (
        f"postgresql+psycopg2://{settings.POSTGRES_USER_TEST}:"
        f"{settings.POSTGRES_PASSWORD_TEST}@{settings.POSTGRES_HOST_TEST}:"
        f"{settings.POSTGRES_PORT_TEST}/{database}"
    )


def _maintenance_url() -> str:
    """Creating and dropping a database cannot run inside that database."""
    return _sync_url("postgres")


def _recreate_scratch_database() -> None:
    engine = sa.create_engine(_maintenance_url(), isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{SCRATCH_DB}" WITH (FORCE)'))
        conn.execute(sa.text(f'CREATE DATABASE "{SCRATCH_DB}"'))
    engine.dispose()


def _drop_scratch_database() -> None:
    engine = sa.create_engine(_maintenance_url(), isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(sa.text(f'DROP DATABASE IF EXISTS "{SCRATCH_DB}" WITH (FORCE)'))
    engine.dispose()


def _relevant(diff) -> bool:
    """Drop diff entries that describe Alembic's own bookkeeping."""
    entries = diff if isinstance(diff, list) else [diff]
    for entry in entries:
        table = None
        if entry[0] in {"add_table", "remove_table"}:
            table = entry[1].name
        elif entry[0] in {"add_index", "remove_index"}:
            table = entry[1].table.name
        elif len(entry) > 2 and isinstance(entry[2], str):
            table = entry[2]
        if table not in IGNORED_TABLES:
            return True
    return False


def _alembic_config(url: str) -> Config:
    config = Config("alembic.ini")
    # env.py reads the target database from `-x db_url`; there is no public
    # API for that beyond the parsed CLI options.
    config.cmd_opts = Namespace(x=[f"db_url={url}"])
    config.attributes["configure_logger"] = False
    return config


@pytest.fixture(scope="module")
def migrated_engine():
    try:
        _recreate_scratch_database()
    except sa.exc.OperationalError as exc:  # pragma: no cover - environment guard
        pytest.skip(f"Postgres not reachable for migration check: {exc}")

    url = _sync_url(SCRATCH_DB)
    command.upgrade(_alembic_config(url), "head")

    engine = sa.create_engine(url)
    try:
        yield engine
    finally:
        engine.dispose()
        _drop_scratch_database()


def test_migrations_can_be_stepped_all_the_way_back_and_forward():
    """An unusable downgrade is only discovered during an incident.

    Runs on its own database so a half-torn-down schema cannot affect the
    other checks in this module.
    """
    _recreate_scratch_database()
    url = _sync_url(SCRATCH_DB)
    config = _alembic_config(url)

    try:
        command.upgrade(config, "head")
        command.downgrade(config, "base")

        engine = sa.create_engine(url)
        with engine.connect() as conn:
            remaining = set(sa.inspect(conn).get_table_names()) - IGNORED_TABLES
        engine.dispose()
        assert remaining == set()

        command.upgrade(config, "head")
    finally:
        _drop_scratch_database()


def test_migrations_produce_the_model_schema(migrated_engine):
    with migrated_engine.connect() as conn:
        context = MigrationContext.configure(
            conn, opts={"compare_type": True, "compare_server_default": True}
        )
        diffs = compare_metadata(context, Base.metadata)

    unexpected = [diff for diff in diffs if _relevant(diff)]
    assert not unexpected, (
        "alembic upgrade head does not reproduce Base.metadata. "
        f"Differences: {unexpected}"
    )


def test_migrations_install_the_integrity_triggers(migrated_engine):
    """Triggers live in raw DDL, so metadata comparison cannot see them."""
    with migrated_engine.connect() as conn:
        rows = conn.execute(
            sa.text("SELECT tgname FROM pg_trigger WHERE NOT tgisinternal")
        ).scalars()
        triggers = set(rows)

    assert EXPECTED_TRIGGERS <= triggers


def test_parent_links_cannot_span_two_family_trees(migrated_engine):
    """The trigger, not the application, is the last word on tree isolation."""
    with migrated_engine.begin() as conn:
        owner_id = conn.execute(
            sa.text(
                "INSERT INTO users (id, username, fullname, password_hash, "
                "created_at, updated_at) VALUES (gen_random_uuid(), "
                "'trigger_owner', 'Trigger Owner', 'x', NOW(), NOW()) "
                "RETURNING id"
            )
        ).scalar_one()

        tree_ids = [
            conn.execute(
                sa.text(
                    "INSERT INTO family_trees (id, name, owner_user_id, "
                    "created_at, updated_at) VALUES (gen_random_uuid(), :name, "
                    ":owner, NOW(), NOW()) RETURNING id"
                ),
                {"name": name, "owner": owner_id},
            ).scalar_one()
            for name in ("Tree A", "Tree B")
        ]

        person_ids = [
            conn.execute(
                sa.text(
                    "INSERT INTO persons (id, tree_id, name, gender, created_at, "
                    "updated_at) VALUES (gen_random_uuid(), :tree_id, :name, "
                    "'male', NOW(), NOW()) RETURNING id"
                ),
                {"tree_id": tree_id, "name": name},
            ).scalar_one()
            for tree_id, name in zip(tree_ids, ("parent", "child"))
        ]

    with migrated_engine.begin() as conn:
        with pytest.raises(sa.exc.IntegrityError, match="same family tree"):
            conn.execute(
                sa.text(
                    "INSERT INTO parent_links (id, parent_id, child_id, "
                    "relationship_type, created_at, updated_at) VALUES "
                    "(gen_random_uuid(), :parent, :child, 'biological', "
                    "NOW(), NOW())"
                ),
                {"parent": person_ids[0], "child": person_ids[1]},
            )
