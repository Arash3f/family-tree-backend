#!/usr/bin/env python3
"""Fail if the committed OpenAPI schema/client drift from the live app.

Regenerates openapi.json and generated/api_client into a temp location and
diffs them against the committed versions. Run from the repository root:

    python scripts/check_openapi_client_sync.py

To refresh after a legitimate API change:

    python scripts/export_openapi_schema.py
    poetry run openapi-python-client generate \\
        --path openapi.json --output-path generated/api_client --overwrite
"""

from __future__ import annotations

import filecmp
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENAPI_JSON = ROOT / "openapi.json"
CLIENT_DIR = ROOT / "generated" / "api_client"


def _load_live_schema() -> dict:
    sys.path.insert(0, str(ROOT))
    from app.main import app

    return app.openapi()


IGNORED_NAMES = {".ruff_cache", "__pycache__"}


def _dir_diff(expected: Path, actual: Path) -> list[str]:
    comparison = filecmp.dircmp(expected, actual, ignore=list(IGNORED_NAMES))
    diffs: list[str] = []

    def _walk(node: filecmp.dircmp, rel: str) -> None:
        for name in node.left_only:
            diffs.append(f"missing: {rel}{name}")
        for name in node.right_only:
            diffs.append(f"unexpected: {rel}{name}")
        for name in node.diff_files:
            diffs.append(f"changed: {rel}{name}")
        for name, sub in node.subdirs.items():
            _walk(sub, f"{rel}{name}/")

    _walk(comparison, "")
    return diffs


def main() -> int:
    if not OPENAPI_JSON.is_file():
        sys.stderr.write(
            "Missing openapi.json. Run scripts/export_openapi_schema.py.\n"
        )
        return 1
    if not CLIENT_DIR.is_dir():
        sys.stderr.write("Missing generated/api_client. Run openapi-python-client.\n")
        return 1

    live_schema = _load_live_schema()
    committed_schema = json.loads(OPENAPI_JSON.read_text(encoding="utf-8"))
    if live_schema != committed_schema:
        sys.stderr.write(
            "openapi.json is out of sync with the live FastAPI app.\n"
            "Re-export with: python scripts/export_openapi_schema.py\n"
        )
        return 1
    print("openapi.json is in sync with the live app")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / "api_client"
        result = subprocess.run(
            [
                "poetry",
                "run",
                "openapi-python-client",
                "generate",
                "--path",
                str(OPENAPI_JSON),
                "--output-path",
                str(tmp_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            sys.stderr.write("openapi-python-client generate failed.\n")
            sys.stderr.write(result.stderr or result.stdout or "")
            return result.returncode or 1

        diffs = _dir_diff(tmp_path, CLIENT_DIR)
        if diffs:
            sys.stderr.write("generated/api_client is out of sync with openapi.json:\n")
            for line in diffs[:50]:
                sys.stderr.write(f"  {line}\n")
            sys.stderr.write(
                "Regenerate with:\n"
                "  poetry run openapi-python-client generate --path openapi.json "
                "--output-path generated/api_client --overwrite\n"
            )
            return 1

    print("generated/api_client is in sync with openapi.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
