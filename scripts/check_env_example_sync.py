#!/usr/bin/env python3
"""Fail if .env.example drifts from AppSettings.

A new setting that never reaches .env.example is invisible to anyone deploying
the service: it works locally on the default and then surprises them in an
environment where the default is wrong. Run from the repository root:

    python scripts/check_env_example_sync.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import AppSettings  # noqa: E402

ENV_EXAMPLE = ROOT / ".env.example"

# Test-only knobs that a deployment never sets.
EXEMPT = {
    "POSTGRES_HOST_TEST",
    "POSTGRES_USER_TEST",
    "POSTGRES_PASSWORD_TEST",
    "POSTGRES_DB_TEST",
    "POSTGRES_PORT_TEST",
}


def _documented_keys() -> set[str]:
    keys: set[str] = set()
    for raw in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        keys.add(line.split("=", 1)[0].strip())
    return keys


def main() -> int:
    if not ENV_EXAMPLE.is_file():
        sys.stderr.write("Missing .env.example\n")
        return 1

    declared = set(AppSettings.model_fields) - EXEMPT
    documented = _documented_keys()

    missing = sorted(declared - documented)
    unknown = sorted(documented - set(AppSettings.model_fields))

    if not missing and not unknown:
        print(".env.example covers every AppSettings field")
        return 0

    if missing:
        sys.stderr.write("Settings missing from .env.example:\n")
        for name in missing:
            sys.stderr.write(f"  + {name}\n")
    if unknown:
        sys.stderr.write("Keys in .env.example with no matching setting:\n")
        for name in unknown:
            sys.stderr.write(f"  - {name}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
