from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .gap_detector import detect_gaps
from .kb import (
    connect,
    create_agent_run,
    create_execution_record,
    finish_agent_run,
    record_gap,
    record_observation,
    route_gaps,
)
from .profile_config import load_profile_data, validate_profile_data
from .profiles import DEFAULT_PROFILES_DIR, PROJECT_ROOT, ProfileError


MAX_OUTPUT_CHARS = 1200
INTERPOLATION_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


class RunBlocked(Exception):
    def __init__(self, message: str, exit_code: int = 2):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


@dataclass(frozen=True)
class ResolvedProfile:
    name: str
    repo_name: str
    repo_root: Path
    commands: dict[str, str]
    reports: dict[str, str]
    artifacts: dict[str, str]
    required_paths: list[str]
    required_reports_after_run: list[str]
    required_artifacts_after_run: list[str]
    risk_area_mappings: dict[str, list[str]]
    analysis_mode: str
    known_evidence_gaps: list[dict[str, str]]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def bounded(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    cleaned = "\n".join(line.rstrip() for line in text.strip().splitlines())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 15].rstrip() + "\n[truncated]"


def interpolate_value(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        env_name = match.group(1)
        configured = os.getenv(env_name)
        if configured:
            return configured
        fallback = match.group(2)
        if fallback is not None:
            return fallback
        raise RunBlocked(f"required environment variable is missing: {env_name}")

    return INTERPOLATION_RE.sub(replace, value)


def ensure_relative_safe(path_value: str, field_name: str) -> str:
    path = Path(path_value)
    if path.is_absolute():
        raise RunBlocked(f"{field_name} must be relative to the target repository: {path_value}")
    if ".." in path.parts:
        raise RunBlocked(f"{field_name} must not escape the target repository: {path_value}")
    return path_value


def resolve_repo_root(raw_root: str) -> Path:
    interpolated = interpolate_value(raw_root)
    path = Path(interpolated).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def _string_map(data: dict[str, Any], key: str) -> dict[str, str]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise RunBlocked(f"profile field '{key}' must be an object")
    result: dict[str, str] = {}
    for item_key, item_value in value.items():
        if not isinstance(item_key, str) or not isinstance(item_value, str):
            raise RunBlocked(f"profile field '{key}' must map strings to strings")
        result[item_key] = item_value
    return result


def _string_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RunBlocked(f"profile field '{key}' must be a list of strings")
    return value


def load_and_validate_profile(
    profile_name: str,
    command_names: list[str],
    profiles_dir: Path = DEFAULT_PROFILES_DIR,
) -> ResolvedProfile:
    try:
        data = load_profile_data(profile_name, profiles_dir)
    except ProfileError as exc:
        raise RunBlocked(str(exc)) from exc

    missing = validate_profile_data(data)
    if missing:
        raise RunBlocked(f"profile '{profile_name}' is missing fields: {', '.join(missing)}")

    repo_root_raw = data.get("repo_root")
    if not isinstance(repo_root_raw, str) or not repo_root_raw:
        raise RunBlocked("profile field 'repo_root' is required")
    repo_root = resolve_repo_root(repo_root_raw)
    if not repo_root.exists() or not repo_root.is_dir():
        raise RunBlocked(f"target repository does not exist: {repo_root}")

    commands = {
        command_name: interpolate_value(command)
        for command_name, command in _string_map(data, "commands").items()
    }
    for command_name in command_names:
        if command_name not in commands or not commands[command_name].strip():
            raise RunBlocked(f"configured command is absent: {command_name}")
        try:
            shlex.split(commands[command_name])
        except ValueError as exc:
            raise RunBlocked(f"configured command is invalid: {command_name}: {exc}") from exc

    reports = _string_map(data, "reports")
    artifacts = _string_map(data, "artifacts")
    for key, path_value in reports.items():
        ensure_relative_safe(path_value, f"reports.{key}")
    for key, path_value in artifacts.items():
        ensure_relative_safe(path_value, f"artifacts.{key}")

    validation = data.get("validation", {})
    if not isinstance(validation, dict):
        raise RunBlocked("profile field 'validation' must be an object")
    required_paths = _string_list(validation, "required_paths")
    required_reports_after_run = _string_list(validation, "required_reports_after_run")
    required_artifacts_after_run = _string_list(validation, "required_artifacts_after_run")
    for path_value in [*required_paths, *required_reports_after_run, *required_artifacts_after_run]:
        ensure_relative_safe(path_value, "validation path")
    missing_paths = [path_value for path_value in required_paths if not (repo_root / path_value).exists()]
    if missing_paths:
        raise RunBlocked(f"required target paths are missing: {', '.join(missing_paths)}")

    raw_mappings = data.get("risk_area_mappings", {})
    if not isinstance(raw_mappings, dict):
        raise RunBlocked("profile field 'risk_area_mappings' must be an object")
    risk_area_mappings: dict[str, list[str]] = {}
    for risk_area, paths in raw_mappings.items():
        if not isinstance(risk_area, str) or not isinstance(paths, list):
            raise RunBlocked("profile field 'risk_area_mappings' must map strings to lists")
        if not all(isinstance(item, str) for item in paths):
            raise RunBlocked("profile field 'risk_area_mappings' must contain path strings")
        for path_value in paths:
            ensure_relative_safe(path_value, "risk_area_mappings path")
        risk_area_mappings[risk_area] = paths

    analysis_mode = data.get("analysis_mode", "python_coverage")
    if analysis_mode not in {"python_coverage", "command_only"}:
        raise RunBlocked("profile field 'analysis_mode' must be 'python_coverage' or 'command_only'")
    raw_known_gaps = data.get("known_evidence_gaps", [])
    if not isinstance(raw_known_gaps, list):
        raise RunBlocked("profile field 'known_evidence_gaps' must be a list")
    known_evidence_gaps: list[dict[str, str]] = []
    for gap in raw_known_gaps:
        if not isinstance(gap, dict) or not all(
            isinstance(gap.get(key), str) and gap[key] for key in ("type", "summary")
        ):
            raise RunBlocked("known evidence gaps require non-empty 'type' and 'summary' strings")
        known_evidence_gaps.append({"type": gap["type"], "summary": gap["summary"]})

    return ResolvedProfile(
        name=str(data.get("name", profile_name)),
        repo_name=str(data.get("repo_name", profile_name)),
        repo_root=repo_root,
        commands=commands,
        reports=reports,
        artifacts=artifacts,
        required_paths=required_paths,
        required_reports_after_run=required_reports_after_run,
        required_artifacts_after_run=required_artifacts_after_run,
        risk_area_mappings=risk_area_mappings,
        analysis_mode=analysis_mode,
        known_evidence_gaps=known_evidence_gaps,
    )


def changed_files(repo_root: Path, base: str, head: str) -> list[str]:
    for args in (["git", "diff", "--name-only", f"{base}...{head}"], ["git", "diff", "--name-only", base, head]):
        result = subprocess.run(args, cwd=repo_root, check=False, capture_output=True, text=True)
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    message = result.stderr.strip() or "git diff failed"
    raise RunBlocked(f"invalid git refs or diff failed: {message}")


def command_refs(profile: ResolvedProfile, command_name: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    report_refs = [
        {
            "kind": key,
            "path": path_value,
            "exists": (profile.repo_root / path_value).exists(),
        }
        for key, path_value in profile.reports.items()
    ]
    artifact_refs = [
        {
            "kind": key,
            "path": path_value,
            "exists": (profile.repo_root / path_value).exists(),
        }
        for key, path_value in profile.artifacts.items()
    ]
    return artifact_refs, report_refs


def run_command(profile: ResolvedProfile, command_name: str, timeout: int) -> dict[str, Any]:
    command = profile.commands[command_name]
    started_at = utc_now()
    start = time.monotonic()
    exit_code: int | None = None
    stdout_summary = ""
    stderr_summary = ""
    status = "passed"
    args = shlex.split(command)

    try:
        result = subprocess.run(
            args,
            cwd=profile.repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        exit_code = result.returncode
        stdout_summary = bounded(result.stdout)
        stderr_summary = bounded(result.stderr)
        if result.returncode != 0:
            status = "failed"
    except FileNotFoundError as exc:
        status = "missing_command"
        stderr_summary = str(exc)
    except subprocess.TimeoutExpired as exc:
        status = "timed_out"
        stdout_summary = bounded(exc.stdout or "")
        stderr_summary = bounded(exc.stderr or "")

    finished_at = utc_now()
    duration_ms = int((time.monotonic() - start) * 1000)
    artifact_refs, report_refs = command_refs(profile, command_name)
    if status == "passed":
        missing_reports = [
            path_value
            for path_value in profile.required_reports_after_run
            if not (profile.repo_root / path_value).exists()
        ]
        if missing_reports:
            status = "missing_report"
            stderr_summary = bounded(f"missing required reports: {', '.join(missing_reports)}")
            artifact_refs, report_refs = command_refs(profile, command_name)
        missing_artifacts = [
            path_value
            for path_value in profile.required_artifacts_after_run
            if not (profile.repo_root / path_value).exists()
        ]
        if missing_artifacts:
            status = "missing_artifact"
            stderr_summary = bounded(f"missing required artifacts: {', '.join(missing_artifacts)}")
            artifact_refs, report_refs = command_refs(profile, command_name)

    return {
        "command_name": command_name,
        "command": command,
        "cwd": str(profile.repo_root),
        "status": status,
        "exit_code": exit_code,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": duration_ms,
        "stdout_summary": stdout_summary,
        "stderr_summary": stderr_summary,
        "artifact_refs": artifact_refs,
        "report_refs": report_refs,
    }


def coverage_files_with_missing_lines(report_path: Path, repo_root: Path) -> dict[str, dict[str, list[int]]]:
    data = json.loads(report_path.read_text(encoding="utf-8"))
    files = data.get("files", {}) if isinstance(data, dict) else {}
    normalized: dict[str, dict[str, list[int]]] = {}
    for raw_path, payload in files.items():
        if not isinstance(payload, dict):
            continue
        path = Path(str(raw_path))
        if path.is_absolute():
            try:
                file_path = path.resolve().relative_to(repo_root).as_posix()
            except ValueError:
                file_path = path.name
        else:
            file_path = path.as_posix()
        missing_lines = payload.get("missing_lines") or []
        covered_lines = payload.get("covered_lines") or payload.get("executed_lines") or []
        normalized[file_path] = {
            "missing_lines": [int(line) for line in missing_lines],
            "covered_lines": [int(line) for line in covered_lines],
        }
    return normalized


def reviewable_next_action(gaps: list[dict[str, Any]]) -> str:
    pricing_gap = next((gap for gap in gaps if "pricing.py" in str(gap["path"])), None)
    if pricing_gap:
        return "Scribe should create a regression test for quantity and discount ordering."
    if gaps:
        return "Scribe should create a regression test for the uncovered changed Python file."
    return "No QA gap action is recommended for this run."


def _status_to_exit(statuses: list[str], run_status: str) -> int:
    if run_status == "abstained":
        return 0
    if "timed_out" in statuses:
        return 3
    if "failed" in statuses:
        return 1
    if any(status in statuses for status in {"missing_command", "missing_report", "missing_artifact", "blocked"}):
        return 2
    return 0


def run_evidence_loop(
    *,
    profile_name: str,
    base: str,
    head: str,
    command_names: list[str] | None = None,
    timeout: int = 120,
    dry_run: bool = False,
    profiles_dir: Path = DEFAULT_PROFILES_DIR,
) -> tuple[int, dict[str, Any]]:
    command_names = command_names or ["unit"]
    profile = load_and_validate_profile(profile_name, command_names, profiles_dir)
    summary: dict[str, Any] = {
        "profile": profile.name,
        "target_repo": str(profile.repo_root),
        "base": base,
        "head": head,
        "changed_files": [],
        "commands": [],
        "reports": [],
        "gaps": [],
        "recommended_next_action": "",
        "status": "planned" if dry_run else "running",
    }

    if dry_run:
        summary["commands"] = [
            {
                "command_name": command_name,
                "command": profile.commands[command_name],
                "status": "planned",
            }
            for command_name in command_names
        ]
        summary["reports"] = [{"path": path_value, "exists": False} for path_value in profile.reports.values()]
        summary["recommended_next_action"] = "Dry run only; no evidence was persisted."
        return 0, summary

    conn = connect()
    run_id = create_agent_run(
        "inspector",
        profile.name,
        trigger=f"run evidence loop {base}..{head}",
        conn=conn,
    )
    summary["run_id"] = run_id
    try:
        files = changed_files(profile.repo_root, base, head)
        summary["changed_files"] = files
        relevant_files = [file_path for file_path in files if file_path.endswith(".py")]
        if profile.analysis_mode == "python_coverage" and not relevant_files:
            record_observation("abstained", "no relevant changed Python files", run_id, conn)
            finish_agent_run(run_id, "abstained", conn)
            summary["status"] = "abstained"
            summary["recommended_next_action"] = "No QA gap action is recommended for this run."
            return 0, summary

        execution_statuses = []
        for command_name in command_names:
            record = run_command(profile, command_name, timeout)
            execution_statuses.append(str(record["status"]))
            create_execution_record(run_id=run_id, conn=conn, **record)
            summary["commands"].append(
                {
                    "command_name": record["command_name"],
                    "status": record["status"],
                    "exit_code": record["exit_code"],
                    "duration_ms": record["duration_ms"],
                }
            )
            summary["reports"] = record["report_refs"]

        if any(status != "passed" for status in execution_statuses):
            status = "blocked"
            record_observation("blocked", f"execution did not produce usable evidence: {', '.join(execution_statuses)}", run_id, conn)
            finish_agent_run(run_id, status, conn)
            summary["status"] = status
            summary["recommended_next_action"] = "Fix deterministic evidence execution before routing QA work."
            return _status_to_exit(execution_statuses, status), summary

        if profile.analysis_mode == "command_only":
            gap_ids = [
                record_gap(gap["type"], "", gap["summary"], conn)
                for gap in profile.known_evidence_gaps
            ]
            routed = route_gaps(conn)
            routed_by_id = {int(row["id"]): dict(row) for row in routed}
            summary["gaps"] = [routed_by_id[gap_id] for gap_id in gap_ids if gap_id in routed_by_id]
            summary["recommended_next_action"] = (
                "Beacon should scope future evidence collection for the known coverage gaps."
                if summary["gaps"]
                else "No QA gap action is recommended for this run."
            )
            if summary["gaps"]:
                record_observation("reviewable_next_action", summary["recommended_next_action"], run_id, conn)
            finish_agent_run(run_id, "acted", conn)
            summary["status"] = "acted"
            return 0, summary

        coverage_report = profile.reports.get("coverage")
        if not coverage_report:
            record_observation("blocked", "coverage report is not configured", run_id, conn)
            finish_agent_run(run_id, "blocked", conn)
            summary["status"] = "blocked"
            summary["recommended_next_action"] = "Configure a coverage report before routing QA work."
            return 2, summary

        coverage_path = profile.repo_root / coverage_report
        coverage = coverage_files_with_missing_lines(coverage_path, profile.repo_root)
        coverage_gaps = detect_gaps(relevant_files, coverage_path=coverage_path)
        gap_ids = []
        for gap_type, path, detail in coverage_gaps:
            if coverage.get(path, {}).get("missing_lines"):
                gap_ids.append(record_gap(gap_type, path, detail, conn))
        routed = route_gaps(conn)
        routed_by_id = {int(row["id"]): dict(row) for row in routed}
        summary["gaps"] = [routed_by_id[gap_id] for gap_id in gap_ids if gap_id in routed_by_id]
        summary["recommended_next_action"] = reviewable_next_action(summary["gaps"])
        if summary["gaps"]:
            record_observation("reviewable_next_action", summary["recommended_next_action"], run_id, conn)
        finish_agent_run(run_id, "acted", conn)
        summary["status"] = "acted"
        return 0, summary
    except RunBlocked as exc:
        record_observation("blocked", exc.message, run_id, conn)
        finish_agent_run(run_id, "blocked", conn)
        summary["status"] = "blocked"
        summary["recommended_next_action"] = exc.message
        return exc.exit_code, summary
    except Exception:
        finish_agent_run(run_id, "blocked", conn)
        raise
    finally:
        conn.close()


def format_text(summary: dict[str, Any]) -> str:
    lines = [
        f"profile: {summary['profile']}",
        f"target_repo: {summary['target_repo']}",
        f"base: {summary['base']}",
        f"head: {summary['head']}",
        f"changed_files: {len(summary.get('changed_files', []))}",
        "commands:",
    ]
    commands = summary.get("commands", [])
    if commands:
        for command in commands:
            parts = [str(command.get("command_name")), str(command.get("status"))]
            if command.get("exit_code") is not None:
                parts.append(f"exit_code={command['exit_code']}")
            if command.get("duration_ms") is not None:
                parts.append(f"duration_ms={command['duration_ms']}")
            lines.append(f"- {parts[0]}: {', '.join(parts[1:])}")
    else:
        lines.append("- none")
    lines.append("reports:")
    reports = summary.get("reports", [])
    if reports:
        for report in reports:
            lines.append(f"- {report.get('path')}: {'found' if report.get('exists') else 'missing'}")
    else:
        lines.append("- none")
    lines.append("gaps:")
    gaps = summary.get("gaps", [])
    if gaps:
        for gap in gaps:
            lines.append(f"- {gap['gap_type']} {gap['path']} -> {gap.get('recommended_agent')}: {gap.get('route_reason')}")
    else:
        lines.append("- none")
    lines.extend(["recommended_next_action:", str(summary.get("recommended_next_action", ""))])
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run deterministic QA evidence collection for a target repo.")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--base", default="main")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--command", action="append", dest="commands")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        exit_code, summary = run_evidence_loop(
            profile_name=args.profile,
            base=args.base,
            head=args.head,
            command_names=args.commands or ["unit"],
            timeout=args.timeout,
            dry_run=args.dry_run,
        )
    except RunBlocked as exc:
        summary = {
            "status": "blocked",
            "profile": args.profile,
            "target_repo": "",
            "base": args.base,
            "head": args.head,
            "changed_files": [],
            "commands": [],
            "reports": [],
            "gaps": [],
            "recommended_next_action": exc.message,
        }
        exit_code = exc.exit_code
    except OSError as exc:
        print(f"qa-agents run: KB persistence failed: {exc}", file=sys.stderr)
        return 4

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(format_text(summary), end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
