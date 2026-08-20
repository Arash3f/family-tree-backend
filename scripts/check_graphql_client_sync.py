#!/usr/bin/env python3
"""Fail if the committed GraphQL schema/client drift from the live app.

Regenerates schema.graphql and generated/graphql_client into a temp location
and diffs them against the committed versions. Run from the repository root:

    python scripts/check_graphql_client_sync.py

To refresh after a legitimate API change:

    python scripts/export_graphql_schema.py
    poetry run ariadne-codegen client
"""

from __future__ import annotations

import filecmp
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_GRAPHQL = ROOT / "schema.graphql"
CLIENT_DIR = ROOT / "generated" / "graphql_client" / "family_tree_graphql_client"

TMP_CONFIG_TEMPLATE = """\
[tool.ariadne-codegen]
schema_path = "{schema_path}"
queries_path = "{queries_path}"
target_package_name = "family_tree_graphql_client"
target_package_path = "{target_package_path}"
client_name = "FamilyTreeGraphQLClient"
async_client = true
"""


def _load_live_schema() -> str:
    sys.path.insert(0, str(ROOT))
    from app.presentation.graphql.schema import schema

    return schema.as_str() + "\n"


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
    if not SCHEMA_GRAPHQL.is_file():
        sys.stderr.write(
            "Missing schema.graphql. Run scripts/export_graphql_schema.py.\n"
        )
        return 1
    if not CLIENT_DIR.is_dir():
        sys.stderr.write(
            "Missing generated/graphql_client. Run poetry run ariadne-codegen client.\n"
        )
        return 1

    live_schema = _load_live_schema()
    committed_schema = SCHEMA_GRAPHQL.read_text(encoding="utf-8")
    if live_schema != committed_schema:
        sys.stderr.write(
            "schema.graphql is out of sync with the live app.\n"
            "Re-export with: python scripts/export_graphql_schema.py\n"
        )
        return 1
    print("schema.graphql is in sync with the live app")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        tmp_target = tmp_path / "graphql_client"
        tmp_target.mkdir()

        tmp_config = tmp_path / "ariadne-codegen.toml"
        tmp_config.write_text(
            TMP_CONFIG_TEMPLATE.format(
                schema_path="schema.graphql",
                queries_path="tests/e2e/graphql/queries",
                target_package_path=tmp_target.as_posix(),
            ),
            encoding="utf-8",
        )

        result = subprocess.run(
            ["poetry", "run", "ariadne-codegen", "--config", str(tmp_config), "client"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            sys.stderr.write("ariadne-codegen generate failed.\n")
            sys.stderr.write(result.stderr or result.stdout or "")
            return result.returncode or 1

        tmp_package = tmp_target / "family_tree_graphql_client"
        diffs = _dir_diff(tmp_package, CLIENT_DIR)
        if diffs:
            sys.stderr.write(
                "generated/graphql_client is out of sync with schema.graphql:\n"
            )
            for line in diffs[:50]:
                sys.stderr.write(f"  {line}\n")
            sys.stderr.write("Regenerate with:\n  poetry run ariadne-codegen client\n")
            return 1

    print("generated/graphql_client is in sync with schema.graphql")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
