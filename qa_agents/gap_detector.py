from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from .kb import record_gap, route_gaps


SURVIVING_STATES = {"survived", "survivor", "timeout", "timed_out"}


def changed_files(base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        result = subprocess.run(
            ["git", "diff", "--name-only", base, head],
            check=False,
            capture_output=True,
            text=True,
        )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git diff failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def coverage_files_with_missing_lines(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    files = data.get("files", {}) if isinstance(data, dict) else {}
    missing: set[str] = set()
    for file_path, payload in files.items():
        if isinstance(payload, dict) and payload.get("missing_lines"):
            missing.add(str(file_path))
    return missing


def surviving_mutations(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = next(
            (data[key] for key in ("mutations", "results", "items") if isinstance(data.get(key), list)),
            [],
        )
    else:
        items = []

    survivors = []
    for item in items:
        if not isinstance(item, dict):
            continue
        state = str(item.get("status") or item.get("state") or item.get("result") or "").lower()
        if state in SURVIVING_STATES:
            survivors.append(item)
    return survivors


def detect_gaps(
    files: list[str],
    coverage_path: Path | None = None,
    mutation_path: Path | None = None,
) -> list[tuple[str, str, str]]:
    gaps: list[tuple[str, str, str]] = []
    changed_python = [file_path for file_path in files if file_path.endswith(".py")]

    if coverage_path:
        missing = coverage_files_with_missing_lines(coverage_path)
        for file_path in changed_python:
            if file_path in missing:
                gaps.append(("missing_unit_test", file_path, "changed Python file has uncovered lines"))
    else:
        for file_path in changed_python:
            gaps.append(("missing_unit_test", file_path, "changed Python file should be reviewed for unit coverage"))

    if mutation_path:
        for mutation in surviving_mutations(mutation_path):
            file_path = str(
                mutation.get("file")
                or mutation.get("path")
                or mutation.get("filename")
                or "unknown"
            )
            if file_path in files or file_path == "unknown":
                gaps.append(("surviving_mutant", file_path, "mutation survived deterministic test run"))
    return gaps


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect narrow, deterministic QA gap records.")
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--coverage", type=Path)
    parser.add_argument("--mutation", type=Path)
    parser.add_argument("--route", action="store_true")
    args = parser.parse_args(argv)

    gaps = detect_gaps(changed_files(args.base, args.head), args.coverage, args.mutation)
    for gap_type, path, detail in gaps:
        record_gap(gap_type, path, detail)
        print(f"{gap_type}: {path} - {detail}")
    if args.route:
        route_gaps()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
