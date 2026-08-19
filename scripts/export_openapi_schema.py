#!/usr/bin/env python3
"""Export the FastAPI OpenAPI schema to a JSON file, without starting the server.

Imports app.main only to read app.openapi() -- the lifespan (DB/MinIO/seed
startup) never runs during a plain import, so this does not require a live
database or object storage connection. Run from the repository root:

    python scripts/export_openapi_schema.py [output_path]

Default output path: openapi.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from app.main import app

    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "openapi.json"
    schema = app.openapi()
    output_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote OpenAPI schema to {output_path}")


if __name__ == "__main__":
    main()
