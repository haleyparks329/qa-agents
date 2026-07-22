import json
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from qa_agents.kb import connect, list_execution_records
from qa_agents.public_export import export_public, validate_public_artifact
from qa_agents.run import RunBlocked, load_and_validate_profile, run_evidence_loop


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def init_website_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "haleyparks329.github.io"
    (repo / "src/pages").mkdir(parents=True)
    (repo / "scripts").mkdir()
    (repo / "package.json").write_text('{"name":"fixture"}\n', encoding="utf-8")
    (repo / "astro.config.ts").write_text("export default {}\n", encoding="utf-8")
    (repo / "src/pages/index.astro").write_text("<h1>Home</h1>\n", encoding="utf-8")
    (repo / "scripts/validate.py").write_text(
        "from pathlib import Path\n"
        "Path('dist').mkdir(exist_ok=True)\n"
        "Path('dist/index.html').write_text('<h1>Home</h1>')\n"
        "print('validated from ' + str(Path.cwd()))\n",
        encoding="utf-8",
    )
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "Test User")
    run_git(repo, "add", ".")
    run_git(repo, "commit", "-m", "website fixture")
    return repo


def make_profile(tmp_path: Path, repo: Path) -> Path:
    profiles_dir = tmp_path / "profiles"
    profile_dir = profiles_dir / "personal_website"
    profile_dir.mkdir(parents=True)
    profile = {
        "name": "personal_website",
        "repo_name": "haleyparks329.github.io",
        "repo_root": str(repo),
        "app_description": "Public portfolio fixture.",
        "key_user_flows": ["visit homepage"],
        "risk_areas": ["broken navigation"],
        "test_priorities": ["build"],
        "constraints": ["deterministic"],
        "commands": {"website_validation": f"{shlex.quote(sys.executable)} scripts/validate.py"},
        "reports": {},
        "artifacts": {"production_build": "dist"},
        "analysis_mode": "command_only",
        "known_evidence_gaps": [
            {
                "type": "missing_browser_evidence",
                "summary": "No browser interaction evidence was collected.",
            }
        ],
        "risk_area_mappings": {"broken navigation": ["src/pages"]},
        "validation": {
            "required_paths": ["package.json", "astro.config.ts", "src/pages"],
            "required_reports_after_run": [],
            "required_artifacts_after_run": ["dist"],
        },
    }
    (profile_dir / "profile.json").write_text(json.dumps(profile), encoding="utf-8")
    return profiles_dir


@pytest.fixture
def isolated_kb(tmp_path, monkeypatch):
    path = tmp_path / "qa.db"
    monkeypatch.setenv("QA_KB_PATH", str(path))
    return path


def test_repository_profile_loads(monkeypatch, tmp_path):
    repo = init_website_repo(tmp_path)
    monkeypatch.setenv("QA_TARGET_REPO_ROOT", str(repo))

    profile = load_and_validate_profile("personal_website", ["website_validation"])

    assert profile.name == "personal_website"
    assert profile.repo_name == "haleyparks329.github.io"
    assert profile.analysis_mode == "command_only"
    assert profile.reports == {}


def test_required_target_paths_are_validated(tmp_path):
    repo = init_website_repo(tmp_path)
    profiles_dir = make_profile(tmp_path, repo)
    (repo / "astro.config.ts").unlink()

    with pytest.raises(RunBlocked, match="required target paths are missing: astro.config.ts"):
        load_and_validate_profile("personal_website", ["website_validation"], profiles_dir)


def test_command_only_run_persists_success_and_structured_gap(tmp_path, isolated_kb):
    repo = init_website_repo(tmp_path)
    profiles_dir = make_profile(tmp_path, repo)

    code, summary = run_evidence_loop(
        profile_name="personal_website",
        base="main",
        head="HEAD",
        command_names=["website_validation"],
        profiles_dir=profiles_dir,
    )

    assert code == 0
    assert summary["status"] == "acted"
    assert summary["commands"][0]["status"] == "passed"
    assert summary["gaps"][0]["gap_type"] == "missing_browser_evidence"
    assert summary["gaps"][0]["recommended_agent"] == "beacon"
    conn = connect(isolated_kb)
    try:
        records = list_execution_records(run_id=summary["run_id"], conn=conn)
        assert records[0]["status"] == "passed"
        assert str(repo) in records[0]["stdout_summary"]
    finally:
        conn.close()


def test_missing_post_run_artifact_is_an_execution_failure(tmp_path, isolated_kb):
    repo = init_website_repo(tmp_path)
    profiles_dir = make_profile(tmp_path, repo)
    (repo / "scripts/validate.py").write_text("print('no build output')\n", encoding="utf-8")

    code, summary = run_evidence_loop(
        profile_name="personal_website",
        base="main",
        head="HEAD",
        command_names=["website_validation"],
        profiles_dir=profiles_dir,
    )

    assert code == 2
    assert summary["status"] == "blocked"
    assert summary["commands"][0]["status"] == "missing_artifact"


def test_public_export_is_private_safe_and_stable(tmp_path, isolated_kb):
    repo = init_website_repo(tmp_path)
    profiles_dir = make_profile(tmp_path, repo)

    first = export_public(
        profile_name="personal_website",
        base="main",
        head="HEAD",
        command_names=["website_validation"],
        stable=True,
        profiles_dir=profiles_dir,
    )
    second = export_public(
        profile_name="personal_website",
        base="main",
        head="HEAD",
        command_names=["website_validation"],
        stable=True,
        profiles_dir=profiles_dir,
    )

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    serialized = json.dumps(first, sort_keys=True)
    assert str(tmp_path) not in serialized
    assert "stdout_summary" not in serialized
    assert first["run"]["status"] == "passed_with_gaps"
    assert first["run"]["started_at"] is None
    assert first["commands"] == [
        {"name": "website_validation", "status": "passed", "exit_code": 0, "duration_ms": 0}
    ]
    assert first["coverage_gaps"][0]["type"] == "missing_browser_evidence"
    assert first["policy"]["autonomous_code_changes"] is False
    validate_public_artifact(first)
