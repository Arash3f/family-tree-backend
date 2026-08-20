#!/usr/bin/env python3
"""Export the Strawberry GraphQL schema to a .graphql SDL file.

Imports app.presentation.graphql.schema only to read schema.as_str() -- the
lifespan (DB/MinIO/seed startup) never runs during a plain import, so this
does not require a live database or object storage connection. Run from the
repository root:

    python scripts/export_graphql_schema.py [output_path]

Default output path: schema.graphql
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from app.presentation.graphql.schema import schema

    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "schema.graphql"
    output_path.write_text(schema.as_str() + "\n", encoding="utf-8")
    print(f"Wrote GraphQL schema to {output_path}")


if __name__ == "__main__":
    main()
