"""Emit GitHub Actions annotations from a pytest JUnit XML report."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: annotate_pytest_junit.py <pytest.xml>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    if not path.is_file():
        print(f"::warning::pytest junit missing: {path}")
        return 0

    root = ET.parse(path).getroot()
    failed: list[tuple[str, str]] = []
    for case in root.iter("testcase"):
        bad = case.find("failure")
        if bad is None:
            bad = case.find("error")
        if bad is None:
            continue
        name = f"{case.get('classname', '')}::{case.get('name', '')}"
        raw = (bad.get("message") or bad.text or "failed").strip()
        msg = raw.splitlines()[0][:240]
        failed.append((name, msg))

    for name, msg in failed[:40]:
        print(f"::error title=pytest::{name} — {msg}")
    if failed:
        print(f"::notice::{len(failed)} failing test case(s) (showing up to 40)")
    else:
        print(
            "::notice::No failed testcases in junit "
            "(exit 1 may be coverage --cov-fail-under)."
        )

    for suite in root.iter("testsuite"):
        print(
            "::notice::pytest suite "
            f"tests={suite.get('tests')} "
            f"failures={suite.get('failures')} "
            f"errors={suite.get('errors')} "
            f"skipped={suite.get('skipped')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
