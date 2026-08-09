#!/usr/bin/env python3
"""Fail if requirements.txt drifts from poetry.lock (via poetry export).

Requires Poetry 2+ with poetry-plugin-export (declared in pyproject.toml
under [tool.poetry.requires-plugins]). Run from the repository root:

    python scripts/check_requirements_sync.py
    # or: poetry run python scripts/check_requirements_sync.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"


def _normalize(text: str) -> list[str]:
    """Strip blank lines and comments for a stable comparison."""
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def main() -> int:
    export = subprocess.run(
        [
            "poetry",
            "export",
            "-f",
            "requirements.txt",
            "--without-hashes",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if export.returncode != 0:
        sys.stderr.write(
            "poetry export failed. Install Poetry 2+ and ensure "
            "poetry-plugin-export is available "
            "(poetry install installs project plugins from "
            "[tool.poetry.requires-plugins]).\n"
        )
        sys.stderr.write(export.stderr or export.stdout or "")
        return export.returncode or 1

    if not REQUIREMENTS.is_file():
        sys.stderr.write(f"Missing {REQUIREMENTS.relative_to(ROOT)}\n")
        return 1

    expected = _normalize(export.stdout)
    actual = _normalize(REQUIREMENTS.read_text(encoding="utf-8"))
    if expected == actual:
        print("requirements.txt is in sync with poetry.lock")
        return 0

    sys.stderr.write(
        "requirements.txt is out of sync with poetry.lock.\n"
        "Re-export with:\n"
        "  poetry export -f requirements.txt --without-hashes "
        "-o requirements.txt\n"
    )
    expected_set = set(expected)
    actual_set = set(actual)
    missing = sorted(expected_set - actual_set)
    extra = sorted(actual_set - expected_set)
    if missing:
        sys.stderr.write("Missing from requirements.txt:\n")
        for line in missing[:30]:
            sys.stderr.write(f"  + {line}\n")
    if extra:
        sys.stderr.write("Extra in requirements.txt:\n")
        for line in extra[:30]:
            sys.stderr.write(f"  - {line}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
