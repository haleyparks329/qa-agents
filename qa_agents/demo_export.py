from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from .kb import connect, list_execution_records
from .run import DEFAULT_PROFILES_DIR, RunBlocked, load_and_validate_profile, run_evidence_loop


DEMO_SCHEMA_VERSION = 1
MAX_DIFF_CHARS = 2400
MAX_ARTIFACT_BYTES = 20_000
ABSOLUTE_PATH_RE = re.compile(r"(^|[\s'\"=])(/Users/|/home/|/private/|[A-Za-z]:\\)")
RAW_LOG_KEYS = {"stdout", "stderr", "stdout_summary", "stderr_summary"}


class DemoExportError(Exception):
    pass


def bounded_text(text: str, limit: int = MAX_DIFF_CHARS) -> str:
    cleaned = "\n".join(line.rstrip() for line in text.strip().splitlines())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 15].rstrip() + "\n[truncated]"


def run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise DemoExportError(result.stderr.strip() or "git command failed")
    return result.stdout


def diff_summary(repo_root: Path, base: str, head: str) -> str:
    output = run_git(repo_root, "diff", "--shortstat", f"{base}...{head}").strip()
    return output or "No file changes."


def diff_excerpt(repo_root: Path, base: str, head: str, files: list[str]) -> str:
    args = ["diff", "--unified=3", f"{base}...{head}", "--", *files]
    return bounded_text(run_git(repo_root, *args))


def count_rows(conn: sqlite3.Connection, table: str, run_id: int | None = None) -> int:
    if run_id is None:
        row = conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
    else:
        row = conn.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE run_id = ?", (run_id,)).fetchone()
    return int(row["count"])


def first_execution_record(conn: sqlite3.Connection, run_id: int) -> dict[str, Any]:
    records = [dict(row) for row in list_execution_records(run_id=run_id, conn=conn)]
    if not records:
        raise DemoExportError("completed run has no execution records")
    return records[0]


def observation_messages(conn: sqlite3.Connection, run_id: int) -> list[str]:
    rows = conn.execute(
        """
        SELECT message FROM observations
        WHERE run_id = ? AND kind = 'reviewable_next_action'
        ORDER BY created_at, id
        """,
        (run_id,),
    )
    return [str(row["message"]) for row in rows]


def sanitized_next_action(message: str) -> str:
    if "quantity and discount ordering" in message.lower():
        return "Create a regression test for quantity and discount ordering."
    return message.removeprefix("Quill should ").strip()


def build_demo_artifact(
    *,
    summary: dict[str, Any],
    execution: dict[str, Any],
    next_action_messages: list[str],
    profile_name: str,
    base: str,
    head: str,
    profile_repo_name: str,
    repo_root: Path,
    stable: bool = False,
    patch_count: int = 0,
    test_count: int = 0,
) -> dict[str, Any]:
    gaps = summary.get("gaps") or []
    if summary.get("status") != "acted":
        raise DemoExportError(f"run did not produce exportable evidence: {summary.get('status')}")
    if not gaps:
        raise DemoExportError("completed run has no routed gap evidence")
    if not next_action_messages:
        raise DemoExportError("completed run has no persisted recommendation observation")

    gap = dict(gaps[0])
    changed_files = list(summary.get("changed_files") or [])
    if not changed_files:
        raise DemoExportError("completed run has no changed files")

    reports = list(summary.get("reports") or [])
    coverage_report = next((report for report in reports if report.get("path") == "artifacts/coverage/unit-coverage.json"), None)
    if not coverage_report:
        coverage_report = next((report for report in reports if report.get("path")), None)
    if not coverage_report or not coverage_report.get("exists"):
        raise DemoExportError("completed run has no found coverage report evidence")

    duration_ms = 0 if stable else int(execution.get("duration_ms") or 0)
    next_action = sanitized_next_action(next_action_messages[-1])

    artifact = {
        "schema_version": DEMO_SCHEMA_VERSION,
        "demo_id": "little-bytes-pricing-discount-order",
        "title": "Quantity and discount ordering",
        "application": {
            "name": "Little Bytes",
            "profile": profile_name,
            "repository": profile_repo_name,
        },
        "scenario": {
            "base": base,
            "head": head,
            "summary": "Pricing logic changed while the existing tests continued to pass.",
        },
        "change": {
            "files": changed_files,
            "diff_summary": diff_summary(repo_root, base, head),
            "diff_excerpt": diff_excerpt(repo_root, base, head, changed_files),
        },
        "execution": {
            "command_name": execution["command_name"],
            "status": execution["status"],
            "exit_code": execution["exit_code"],
            "duration_ms": duration_ms,
            "test_summary": "Configured unit tests passed and produced normalized coverage evidence.",
        },
        "evidence": {
            "coverage_report_found": True,
            "coverage_report_path": str(coverage_report["path"]),
            "gap_type": gap["gap_type"],
            "gap_path": gap["path"],
            "gap_detail": gap["detail"],
        },
        "recommendation": {
            "agent": gap["recommended_agent"],
            "route_reason": gap["route_reason"],
            "next_action": next_action,
        },
        "safety": {
            "tests_generated": test_count,
            "patches_generated": patch_count,
            "agents_dispatched": 0,
            "human_review_required": True,
        },
    }
    validate_demo_artifact(artifact)
    return artifact


def iter_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for key, item in value.items():
            strings.extend(iter_strings(key))
            strings.extend(iter_strings(item))
        return strings
    if isinstance(value, list):
        strings = []
        for item in value:
            strings.extend(iter_strings(item))
        return strings
    return []


def reject_absolute_or_private_strings(artifact: dict[str, Any]) -> None:
    for text in iter_strings(artifact):
        if ABSOLUTE_PATH_RE.search(text):
            raise DemoExportError("demo artifact contains an absolute or private-looking path")
        if "QA_KB_PATH" in text or "QA_TARGET_REPO_ROOT" in text:
            raise DemoExportError("demo artifact contains environment variable names")


def validate_relative_paths(paths: list[str], field_name: str) -> None:
    for path_value in paths:
        path = Path(path_value)
        if path.is_absolute() or ".." in path.parts:
            raise DemoExportError(f"{field_name} must contain repository-relative paths")


def validate_demo_artifact(artifact: dict[str, Any]) -> None:
    required = [
        "schema_version",
        "demo_id",
        "title",
        "application",
        "scenario",
        "change",
        "execution",
        "evidence",
        "recommendation",
        "safety",
    ]
    missing = [key for key in required if key not in artifact]
    if missing:
        raise DemoExportError(f"demo artifact is missing required fields: {', '.join(missing)}")

    if artifact["schema_version"] != DEMO_SCHEMA_VERSION:
        raise DemoExportError("unsupported demo artifact schema version")

    for key in RAW_LOG_KEYS:
        if key in artifact:
            raise DemoExportError("demo artifact must not export raw logs")

    validate_relative_paths(list(artifact["change"].get("files") or []), "change.files")
    validate_relative_paths([str(artifact["evidence"].get("coverage_report_path", ""))], "coverage_report_path")
    validate_relative_paths([str(artifact["evidence"].get("gap_path", ""))], "gap_path")

    safety = artifact["safety"]
    for key in ("tests_generated", "patches_generated", "agents_dispatched"):
        if not isinstance(safety.get(key), int):
            raise DemoExportError(f"safety.{key} must be numeric")
    if artifact["recommendation"].get("agent") != "quill":
        raise DemoExportError("demo recommendation must come from persisted Quill routing evidence")
    if artifact["evidence"].get("gap_type") != "missing_unit_test":
        raise DemoExportError("demo evidence must preserve the missing_unit_test gap")

    reject_absolute_or_private_strings(artifact)

    encoded = json.dumps(artifact, sort_keys=True)
    if len(encoded.encode("utf-8")) > MAX_ARTIFACT_BYTES:
        raise DemoExportError("demo artifact is too large for public replay")


def export_demo(
    *,
    profile_name: str,
    base: str,
    head: str,
    output: Path | None = None,
    stable: bool = False,
    profiles_dir: Path = DEFAULT_PROFILES_DIR,
) -> dict[str, Any]:
    profile = load_and_validate_profile(profile_name, ["unit"], profiles_dir)
    code, summary = run_evidence_loop(
        profile_name=profile_name,
        base=base,
        head=head,
        command_names=["unit"],
        profiles_dir=profiles_dir,
    )
    if code != 0:
        raise DemoExportError(f"evidence run failed with exit code {code}: {summary.get('recommended_next_action')}")
    run_id = summary.get("run_id")
    if not isinstance(run_id, int):
        raise DemoExportError("completed run did not expose a run id")

    conn = connect()
    try:
        execution = first_execution_record(conn, run_id)
        messages = observation_messages(conn, run_id)
        artifact = build_demo_artifact(
            summary=summary,
            execution=execution,
            next_action_messages=messages,
            profile_name=profile.name,
            base=base,
            head=head,
            profile_repo_name=f"haleyparks329/{profile.repo_root.name}",
            repo_root=profile.repo_root,
            stable=stable,
            patch_count=count_rows(conn, "patches", run_id),
            test_count=0,
        )
    finally:
        conn.close()

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export a public-safe demo artifact from a real QA Agents run.")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--base", default="main")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stable", action="store_true", help="Normalize dynamic values for committed snapshots.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        artifact = export_demo(
            profile_name=args.profile,
            base=args.base,
            head=args.head,
            output=args.output,
            stable=args.stable,
        )
    except (DemoExportError, RunBlocked, OSError) as exc:
        print(f"qa-agents export-demo: {exc}", file=os.sys.stderr)
        return 2
    print(json.dumps({"output": str(args.output), "demo_id": artifact["demo_id"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
