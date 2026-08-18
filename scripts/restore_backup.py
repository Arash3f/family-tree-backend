#!/usr/bin/env python3
"""Restore a Postgres + Neo4j backup pair created by `backup.database`.

The two dumps are independent snapshots taken back-to-back (see M4 in
REVIEW.md) — restoring both from the same --timestamp gets you as close to a
consistent point in time as the current backup strategy allows, but writes
between the two dump calls can still land on only one side. Verify
application-level consistency after restoring.

Usage (run from the repository root, against a stopped or maintenance-mode app):

    python scripts/restore_backup.py --timestamp 2026-08-18_02-00-00

    # Only one side, e.g. re-seeding Neo4j after a reconciliation disaster:
    python scripts/restore_backup.py --timestamp 2026-08-18_02-00-00 --only postgres
    python scripts/restore_backup.py --timestamp 2026-08-18_02-00-00 --only neo4j
"""

from __future__ import annotations

import argparse
import os
import subprocess  # nosec B404
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402


def restore_postgres(timestamp: str, *, backup_dir: Path) -> None:
    dump_file = backup_dir / f"backup_{timestamp}.sql"
    if not dump_file.exists():
        raise FileNotFoundError(f"Postgres dump not found: {dump_file}")

    env = os.environ.copy()
    env["PGPASSWORD"] = settings.POSTGRES_PASSWORD

    cmd = [
        "pg_restore",
        "-U",
        str(settings.POSTGRES_USER),
        "-h",
        str(settings.POSTGRES_HOST),
        "-p",
        str(settings.POSTGRES_PORT),
        "-d",
        str(settings.POSTGRES_DB),
        "--clean",
        "--if-exists",
        "--no-owner",
        str(dump_file),
    ]

    print(f"Restoring Postgres from {dump_file} ...")
    subprocess.run(cmd, check=True, env=env, timeout=600)  # nosec B603
    print("Postgres restore completed.")


def restore_neo4j(timestamp: str, *, backup_dir: Path) -> None:
    from neo4j import GraphDatabase
    from neo4j_backup import Importer

    neo_backup_dir = backup_dir / f"neo_{timestamp}"
    if not neo_backup_dir.exists():
        raise FileNotFoundError(f"Neo4j backup directory not found: {neo_backup_dir}")

    # neo4j_backup's Importer only supports the SYNC driver API, so this
    # script opens its own dedicated sync driver rather than reaching into
    # the app's request-path `neo4j_client` (which wraps an ASYNC driver
    # since the sync-to-async Neo4j migration).
    driver = GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    )

    print(f"Restoring Neo4j from {neo_backup_dir} ...")
    try:
        importer = Importer(
            project_dir=str(neo_backup_dir),
            driver=driver,
            database="neo4j",
            input_yes=True,
        )
        importer.import_data()
    finally:
        driver.close()
    print("Neo4j restore completed.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timestamp",
        required=True,
        help="Backup timestamp, e.g. 2026-08-18_02-00-00 (matches backup_<ts>.sql "
        "and neo_<ts>/)",
    )
    parser.add_argument(
        "--only",
        choices=["postgres", "neo4j"],
        help="Restore only one side instead of both.",
    )
    args = parser.parse_args()

    backup_dir = Path(settings.BACKUP_DIR)

    if args.only in (None, "postgres"):
        restore_postgres(args.timestamp, backup_dir=backup_dir)
    if args.only in (None, "neo4j"):
        restore_neo4j(args.timestamp, backup_dir=backup_dir)


if __name__ == "__main__":
    main()
