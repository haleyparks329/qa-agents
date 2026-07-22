from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .demo_export import DemoExportError, reject_absolute_or_private_strings
from .kb import connect, list_execution_records
from .profiles import DEFAULT_PROFILES_DIR
from .run import RunBlocked, load_and_validate_profile, run_evidence_loop


PUBLIC_SCHEMA_VERSION = "1.0"
MAX_PUBLIC_ARTIFACT_BYTES = 20_000
PUBLIC_OUTPUT_ENV_VAR = "QA_PUBLIC_ARTIFACT_OUTPUT"


def resolve_public_output(output: Path | None) -> Path:
    configured = output or (Path(value) if (value := os.getenv(PUBLIC_OUTPUT_ENV_VAR)) else None)
    if configured is None:
        raise DemoExportError(
            f"public artifact output is required; pass --output or set {PUBLIC_OUTPUT_ENV_VAR}"
        )
    resolved = configured.expanduser()
    if resolved.exists() and resolved.is_dir():
        raise DemoExportError(f"public artifact output must be a file, not a directory: {resolved}")
    if resolved.suffix.lower() != ".json":
        raise DemoExportError("public artifact output must use a .json extension")
    if resolved.parent.exists() and not resolved.parent.is_dir():
        raise DemoExportError(f"public artifact parent is not a directory: {resolved.parent}")
    return resolved


def write_public_artifact(output: Path, artifact: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent, prefix=f".{output.name}.", delete=False
        ) as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
            temporary_path = Path(handle.name)
        os.replace(temporary_path, output)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def git_revision(repo_root: Path, ref: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", ref], cwd=repo_root, check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise DemoExportError(result.stderr.strip() or f"could not resolve git ref: {ref}")
    return result.stdout.strip()


def validate_public_artifact(artifact: dict[str, Any]) -> None:
    required = {"schema_version", "target", "run", "commands", "findings", "coverage_gaps", "policy"}
    missing = sorted(required.difference(artifact))
    if missing:
        raise DemoExportError(f"public artifact is missing required fields: {', '.join(missing)}")
    if artifact["schema_version"] != PUBLIC_SCHEMA_VERSION:
        raise DemoExportError("unsupported public artifact schema version")
    forbidden_keys = {"command", "cwd", "stdout", "stderr", "stdout_summary", "stderr_summary", "run_id"}

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            if forbidden_keys.intersection(value):
                raise DemoExportError("public artifact contains private execution fields")
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(artifact)
    reject_absolute_or_private_strings(artifact)
    if len(json.dumps(artifact, sort_keys=True).encode("utf-8")) > MAX_PUBLIC_ARTIFACT_BYTES:
        raise DemoExportError("public artifact is too large")


def build_public_artifact(
    *,
    summary: dict[str, Any],
    executions: list[dict[str, Any]],
    repository: str,
    base: str,
    head: str,
    commit: str,
    stable: bool = False,
) -> dict[str, Any]:
    if summary.get("status") != "acted":
        raise DemoExportError(f"run did not produce exportable evidence: {summary.get('status')}")
    commands = [
        {
            "name": str(record["command_name"]),
            "status": str(record["status"]),
            "exit_code": record["exit_code"],
            "duration_ms": 0 if stable else int(record["duration_ms"] or 0),
        }
        for record in executions
    ]
    gaps = [
        {"type": str(gap["gap_type"]), "summary": str(gap["detail"])}
        for gap in summary.get("gaps", [])
    ]
    started_at = None if stable else min((record["started_at"] for record in executions), default=None)
    completed_at = None if stable else max((record["finished_at"] for record in executions), default=None)
    artifact = {
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "target": {"profile": summary["profile"], "repository": repository},
        "run": {
            "status": "passed_with_gaps" if gaps else "passed",
            "base": base,
            "head": head,
            "commit": commit,
            "started_at": started_at,
            "completed_at": completed_at,
        },
        "commands": commands,
        "findings": [],
        "coverage_gaps": gaps,
        "policy": {
            "outcome": "acted",
            "action": "published_review_evidence",
            "autonomous_code_changes": False,
        },
    }
    validate_public_artifact(artifact)
    return artifact


def export_public(
    *,
    profile_name: str,
    base: str,
    head: str,
    command_names: list[str],
    output: Path | None = None,
    stable: bool = False,
    timeout: int = 120,
    profiles_dir: Path = DEFAULT_PROFILES_DIR,
) -> dict[str, Any]:
    profile = load_and_validate_profile(profile_name, command_names, profiles_dir)
    code, summary = run_evidence_loop(
        profile_name=profile_name,
        base=base,
        head=head,
        command_names=command_names,
        timeout=timeout,
        profiles_dir=profiles_dir,
    )
    if code != 0:
        raise DemoExportError(f"evidence run failed with exit code {code}: {summary.get('recommended_next_action')}")
    run_id = summary.get("run_id")
    if not isinstance(run_id, int):
        raise DemoExportError("completed run did not expose a run id")
    conn = connect()
    try:
        executions = [dict(row) for row in list_execution_records(run_id=run_id, conn=conn)]
    finally:
        conn.close()
    if not executions:
        raise DemoExportError("completed run has no execution records")
    artifact = build_public_artifact(
        summary=summary,
        executions=executions,
        repository=profile.repo_name,
        base=base,
        head=head,
        commit=git_revision(profile.repo_root, head),
        stable=stable,
    )
    if output:
        write_public_artifact(resolve_public_output(output), artifact)
    return artifact


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run evidence collection and export a public-safe artifact.")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--base", default="main")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--command", action="append", dest="commands", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        help=f"Destination JSON path (defaults to ${PUBLIC_OUTPUT_ENV_VAR}).",
    )
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--stable", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output = resolve_public_output(args.output)
        artifact = export_public(
            profile_name=args.profile,
            base=args.base,
            head=args.head,
            command_names=args.commands,
            output=output,
            stable=args.stable,
            timeout=args.timeout,
        )
    except (DemoExportError, RunBlocked, OSError) as exc:
        print(f"qa-agents export-public: {exc}", file=os.sys.stderr)
        return 2
    print(json.dumps({"output": str(output), "status": artifact["run"]["status"]}, sort_keys=True))
    return 0
