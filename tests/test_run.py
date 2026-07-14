import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from qa_agents.kb import connect, list_execution_records, list_open_gaps
from qa_agents.run import RunBlocked, coverage_files_with_missing_lines, run_evidence_loop


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def init_target_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "little-bytes"
    (repo / "backend/app").mkdir(parents=True)
    (repo / "backend/tests/unit").mkdir(parents=True)
    (repo / "scripts").mkdir()
    (repo / "backend/app/pricing.py").write_text("def total(quantity, price):\n    return quantity * price\n", encoding="utf-8")
    (repo / "backend/tests/unit/test_placeholder.py").write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "Test User")
    run_git(repo, "add", ".")
    run_git(repo, "commit", "-m", "initial")
    run_git(repo, "checkout", "-b", "pricing-change")
    (repo / "backend/app/pricing.py").write_text(
        "def total(quantity, price, discount):\n    subtotal = quantity * price\n    return subtotal - discount\n",
        encoding="utf-8",
    )
    run_git(repo, "add", ".")
    run_git(repo, "commit", "-m", "change pricing")
    return repo


def write_command_script(repo: Path, body: str, name: str = "write_coverage.py") -> Path:
    script = repo / "scripts" / name
    script.write_text(body, encoding="utf-8")
    return script


def make_profiles_dir(tmp_path: Path, repo: Path, command: str | None = None) -> Path:
    profiles_dir = tmp_path / "profiles"
    profile_dir = profiles_dir / "little_bytes"
    profile_dir.mkdir(parents=True)
    profile = {
        "name": "little_bytes",
        "repo_root": str(repo),
        "app_description": "Temporary Little Bytes fixture.",
        "key_user_flows": ["checkout"],
        "risk_areas": ["pricing accuracy"],
        "test_priorities": ["pricing"],
        "constraints": ["deterministic"],
        "commands": {"unit": command or f"{shlex.quote(sys.executable)} scripts/write_coverage.py"},
        "reports": {"coverage": "artifacts/coverage/unit-coverage.json"},
        "artifacts": {"root": "artifacts"},
        "risk_area_mappings": {"pricing accuracy": ["backend/app/pricing.py"]},
        "validation": {
            "required_paths": ["backend/app", "backend/tests/unit"],
            "required_reports_after_run": ["artifacts/coverage/unit-coverage.json"],
        },
    }
    (profile_dir / "profile.json").write_text(json.dumps(profile), encoding="utf-8")
    return profiles_dir


def coverage_script() -> str:
    return """
from pathlib import Path
import json

path = Path("artifacts/coverage/unit-coverage.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps({
    "files": {
        "backend/app/pricing.py": {
            "executed_lines": [1],
            "missing_lines": [2, 3]
        }
    }
}), encoding="utf-8")
print("coverage written")
"""


@pytest.fixture
def isolated_kb(tmp_path, monkeypatch):
    path = tmp_path / "qa.db"
    monkeypatch.setenv("QA_KB_PATH", str(path))
    return path


def test_valid_dry_run_with_real_profile(tmp_path, monkeypatch, isolated_kb):
    repo = init_target_repo(tmp_path)
    monkeypatch.setenv("QA_TARGET_REPO_ROOT", str(repo))

    code, summary = run_evidence_loop(
        profile_name="little_bytes",
        base="main",
        head="HEAD",
        dry_run=True,
    )

    assert code == 0
    assert summary["status"] == "planned"
    assert summary["commands"][0]["status"] == "planned"
    assert summary["target_repo"] == str(repo.resolve())


def test_missing_target_repository_blocks(tmp_path, isolated_kb):
    profiles_dir = make_profiles_dir(tmp_path, tmp_path / "missing")

    with pytest.raises(RunBlocked, match="target repository does not exist"):
        run_evidence_loop(
            profile_name="little_bytes",
            base="main",
            head="HEAD",
            profiles_dir=profiles_dir,
        )


def test_invalid_profile_blocks(tmp_path, isolated_kb):
    profiles_dir = tmp_path / "profiles"
    profile_dir = profiles_dir / "little_bytes"
    profile_dir.mkdir(parents=True)
    (profile_dir / "profile.json").write_text(json.dumps({"name": "little_bytes"}), encoding="utf-8")

    with pytest.raises(RunBlocked, match="missing fields"):
        run_evidence_loop(
            profile_name="little_bytes",
            base="main",
            head="HEAD",
            profiles_dir=profiles_dir,
        )


def test_missing_required_path_blocks(tmp_path, isolated_kb):
    repo = init_target_repo(tmp_path)
    profiles_dir = make_profiles_dir(tmp_path, repo)
    (repo / "backend/tests/unit").rename(repo / "backend/tests/moved")

    with pytest.raises(RunBlocked, match="required target paths are missing"):
        run_evidence_loop(
            profile_name="little_bytes",
            base="main",
            head="HEAD",
            profiles_dir=profiles_dir,
        )


def test_invalid_git_ref_is_blocked_run(tmp_path, isolated_kb):
    repo = init_target_repo(tmp_path)
    write_command_script(repo, coverage_script())
    profiles_dir = make_profiles_dir(tmp_path, repo)

    code, summary = run_evidence_loop(
        profile_name="little_bytes",
        base="does-not-exist",
        head="HEAD",
        profiles_dir=profiles_dir,
    )

    assert code == 2
    assert summary["status"] == "blocked"
    assert "invalid git refs" in summary["recommended_next_action"]


def test_no_relevant_changed_files_abstains(tmp_path, isolated_kb):
    repo = init_target_repo(tmp_path)
    run_git(repo, "checkout", "main")
    run_git(repo, "checkout", "-b", "docs-change")
    (repo / "README.md").write_text("docs\n", encoding="utf-8")
    run_git(repo, "add", ".")
    run_git(repo, "commit", "-m", "docs")
    write_command_script(repo, "raise SystemExit('should not run')\n")
    profiles_dir = make_profiles_dir(tmp_path, repo)

    code, summary = run_evidence_loop(
        profile_name="little_bytes",
        base="main",
        head="HEAD",
        profiles_dir=profiles_dir,
    )

    assert code == 0
    assert summary["status"] == "abstained"
    assert summary["commands"] == []


def test_successful_pricing_change_persists_execution_gap_and_scribe_route(tmp_path, isolated_kb):
    repo = init_target_repo(tmp_path)
    write_command_script(repo, coverage_script())
    profiles_dir = make_profiles_dir(tmp_path, repo)

    code, summary = run_evidence_loop(
        profile_name="little_bytes",
        base="main",
        head="HEAD",
        profiles_dir=profiles_dir,
    )

    assert code == 0
    assert summary["status"] == "acted"
    assert summary["commands"][0]["status"] == "passed"
    assert summary["gaps"] == [
        {
            "id": summary["gaps"][0]["id"],
            "gap_type": "missing_unit_test",
            "path": "backend/app/pricing.py",
            "detail": "changed Python file has uncovered lines",
            "status": "open",
            "recommended_agent": "scribe",
            "route_reason": "test authoring gap",
        }
    ]
    assert summary["recommended_next_action"] == "Scribe should create a regression test for quantity and discount ordering."

    conn = connect(isolated_kb)
    records = list_execution_records(conn=conn)
    gaps = list_open_gaps(conn)
    assert records[0]["command_name"] == "unit"
    assert records[0]["status"] == "passed"
    assert gaps[0]["recommended_agent"] == "scribe"


def test_failed_command_records_execution_and_exits_one(tmp_path, isolated_kb):
    repo = init_target_repo(tmp_path)
    write_command_script(repo, "print('nope')\nraise SystemExit(5)\n")
    profiles_dir = make_profiles_dir(tmp_path, repo)

    code, summary = run_evidence_loop(
        profile_name="little_bytes",
        base="main",
        head="HEAD",
        profiles_dir=profiles_dir,
    )

    assert code == 1
    assert summary["commands"][0]["status"] == "failed"
    assert summary["status"] == "blocked"


def test_timeout_records_execution_and_exits_three(tmp_path, isolated_kb):
    repo = init_target_repo(tmp_path)
    write_command_script(repo, "import time\ntime.sleep(2)\n")
    profiles_dir = make_profiles_dir(tmp_path, repo)

    code, summary = run_evidence_loop(
        profile_name="little_bytes",
        base="main",
        head="HEAD",
        timeout=1,
        profiles_dir=profiles_dir,
    )

    assert code == 3
    assert summary["commands"][0]["status"] == "timed_out"


def test_missing_command_records_execution(tmp_path, isolated_kb):
    repo = init_target_repo(tmp_path)
    profiles_dir = make_profiles_dir(tmp_path, repo, command="missing-little-bytes-command")

    code, summary = run_evidence_loop(
        profile_name="little_bytes",
        base="main",
        head="HEAD",
        profiles_dir=profiles_dir,
    )

    assert code == 2
    assert summary["commands"][0]["status"] == "missing_command"


def test_missing_coverage_report_blocks(tmp_path, isolated_kb):
    repo = init_target_repo(tmp_path)
    write_command_script(repo, "print('no coverage')\n")
    profiles_dir = make_profiles_dir(tmp_path, repo)

    code, summary = run_evidence_loop(
        profile_name="little_bytes",
        base="main",
        head="HEAD",
        profiles_dir=profiles_dir,
    )

    assert code == 2
    assert summary["commands"][0]["status"] == "missing_report"


def test_coverage_ingestion_normalizes_fixture(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    report = repo / "coverage.json"
    report.write_text(
        json.dumps({"files": {"backend/app/pricing.py": {"covered_lines": [1], "missing_lines": [2]}}}),
        encoding="utf-8",
    )

    assert coverage_files_with_missing_lines(report, repo)["backend/app/pricing.py"]["missing_lines"] == [2]


def test_json_cli_output_for_dry_run(tmp_path, monkeypatch, isolated_kb):
    repo = init_target_repo(tmp_path)
    monkeypatch.setenv("QA_TARGET_REPO_ROOT", str(repo))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "qa_agents",
            "run",
            "--profile",
            "little_bytes",
            "--base",
            "main",
            "--head",
            "HEAD",
            "--dry-run",
            "--json",
        ],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "QA_KB_PATH": str(isolated_kb), "QA_TARGET_REPO_ROOT": str(repo)},
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["profile"] == "little_bytes"
    assert payload["status"] == "planned"
