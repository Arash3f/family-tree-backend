#!/usr/bin/env python3
"""Fail if requirements exports drift from poetry.lock.

Requires Poetry 2+ with poetry-plugin-export (declared in pyproject.toml
under [tool.poetry.requires-plugins]). Run from the repository root:

    python scripts/check_requirements_sync.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKS = (
    (
        ROOT / "requirements.txt",
        ["poetry", "export", "-f", "requirements.txt", "--without-hashes"],
    ),
    (
        ROOT / "requirements-dev.txt",
        [
            "poetry",
            "export",
            "-f",
            "requirements.txt",
            "--without-hashes",
            "--only",
            "dev",
        ],
    ),
)


def _normalize(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def _check_one(path: Path, export_cmd: list[str]) -> int:
    export = subprocess.run(
        export_cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if export.returncode != 0:
        sys.stderr.write(
            f"poetry export failed for {path.name}. Install Poetry 2+ and "
            "poetry-plugin-export "
            "([tool.poetry.requires-plugins]).\n"
        )
        sys.stderr.write(export.stderr or export.stdout or "")
        return export.returncode or 1

    if not path.is_file():
        sys.stderr.write(f"Missing {path.relative_to(ROOT)}\n")
        return 1

    expected = _normalize(export.stdout)
    actual = _normalize(path.read_text(encoding="utf-8"))
    if expected == actual:
        print(f"{path.name} is in sync with poetry.lock")
        return 0

    sys.stderr.write(
        f"{path.name} is out of sync with poetry.lock.\n"
        "Re-export with:\n"
        f"  {' '.join(export_cmd)} -o {path.name}\n"
    )
    expected_set = set(expected)
    actual_set = set(actual)
    missing = sorted(expected_set - actual_set)
    extra = sorted(actual_set - expected_set)
    if missing:
        sys.stderr.write(f"Missing from {path.name}:\n")
        for line in missing[:30]:
            sys.stderr.write(f"  + {line}\n")
    if extra:
        sys.stderr.write(f"Extra in {path.name}:\n")
        for line in extra[:30]:
            sys.stderr.write(f"  - {line}\n")
    return 1


def main() -> int:
    code = 0
    for path, cmd in CHECKS:
        result = _check_one(path, cmd)
        if result != 0:
            code = result
    return code


if __name__ == "__main__":
    raise SystemExit(main())
