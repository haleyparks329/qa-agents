import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from qa_agents.demo_export import DemoExportError, export_demo, validate_demo_artifact


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def init_demo_repo(tmp_path: Path, missing_lines: list[int] | None = None) -> Path:
    repo = tmp_path / "little-bytes"
    (repo / "backend/app").mkdir(parents=True)
    (repo / "backend/tests/unit").mkdir(parents=True)
    (repo / "scripts").mkdir()
    (repo / "backend/app/pricing.py").write_text(
        "def total(quantity, price):\n    return quantity * price\n",
        encoding="utf-8",
    )
    (repo / "backend/tests/unit/test_placeholder.py").write_text(
        "def test_placeholder():\n    assert True\n",
        encoding="utf-8",
    )
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "Test User")
    run_git(repo, "add", ".")
    run_git(repo, "commit", "-m", "baseline")
    run_git(repo, "checkout", "-b", "scenario/pricing-discount-order")
    (repo / "backend/app/pricing.py").write_text(
        "def total(quantity, price, discount):\n"
        "    subtotal = quantity * price\n"
        "    return subtotal - discount\n",
        encoding="utf-8",
    )
    run_git(repo, "add", ".")
    run_git(repo, "commit", "-m", "change pricing")

    missing = missing_lines if missing_lines is not None else [2, 3]
    script = repo / "scripts" / "write_coverage.py"
    script.write_text(
        "\n".join(
            [
                "from pathlib import Path",
                "import json",
                "path = Path('artifacts/coverage/unit-coverage.json')",
                "path.parent.mkdir(parents=True, exist_ok=True)",
                "path.write_text(json.dumps({'files': {'backend/app/pricing.py': {'executed_lines': [1], 'missing_lines': "
                + repr(missing)
                + "}}}), encoding='utf-8')",
                "print('raw log with local path should stay out of the demo artifact')",
            ]
        ),
        encoding="utf-8",
    )
    return repo


def make_profiles_dir(tmp_path: Path, repo: Path) -> Path:
    profiles_dir = tmp_path / "profiles"
    profile_dir = profiles_dir / "little_bytes"
    profile_dir.mkdir(parents=True)
    profile = {
        "name": "little_bytes",
        "repo_name": "little-bytes",
        "repo_root": str(repo),
        "app_description": "Temporary Little Bytes fixture.",
        "key_user_flows": ["checkout"],
        "risk_areas": ["pricing accuracy"],
        "test_priorities": ["pricing"],
        "constraints": ["deterministic"],
        "commands": {"unit": f"{shlex.quote(sys.executable)} scripts/write_coverage.py"},
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


@pytest.fixture
def isolated_kb(tmp_path, monkeypatch):
    path = tmp_path / "qa.db"
    monkeypatch.setenv("QA_KB_PATH", str(path))
    return path


def test_successful_little_bytes_demo_export_preserves_evidence(tmp_path, isolated_kb):
    repo = init_demo_repo(tmp_path)
    profiles_dir = make_profiles_dir(tmp_path, repo)

    artifact = export_demo(
        profile_name="little_bytes",
        base="main",
        head="scenario/pricing-discount-order",
        stable=True,
        profiles_dir=profiles_dir,
    )

    assert artifact["change"]["files"] == ["backend/app/pricing.py"]
    assert artifact["execution"]["status"] == "passed"
    assert artifact["execution"]["exit_code"] == 0
    assert artifact["execution"]["duration_ms"] == 0
    assert artifact["evidence"]["coverage_report_found"] is True
    assert artifact["evidence"]["gap_type"] == "missing_unit_test"
    assert artifact["evidence"]["gap_path"] == "backend/app/pricing.py"
    assert artifact["recommendation"]["agent"] == "scribe"
    assert artifact["recommendation"]["route_reason"] == "test authoring gap"
    assert artifact["safety"]["tests_generated"] == 0
    assert artifact["safety"]["patches_generated"] == 0
    assert artifact["safety"]["agents_dispatched"] == 0
    validate_demo_artifact(artifact)


def test_demo_export_does_not_include_absolute_paths_or_raw_logs(tmp_path, isolated_kb):
    repo = init_demo_repo(tmp_path)
    profiles_dir = make_profiles_dir(tmp_path, repo)

    artifact = export_demo(
        profile_name="little_bytes",
        base="main",
        head="scenario/pricing-discount-order",
        stable=True,
        profiles_dir=profiles_dir,
    )
    serialized = json.dumps(artifact, sort_keys=True)

    assert str(tmp_path) not in serialized
    assert "stdout_summary" not in serialized
    assert "stderr_summary" not in serialized
    assert "raw log with local path" not in serialized


def test_stable_demo_export_has_stable_json_ordering(tmp_path, isolated_kb):
    repo = init_demo_repo(tmp_path)
    profiles_dir = make_profiles_dir(tmp_path, repo)

    first = export_demo(
        profile_name="little_bytes",
        base="main",
        head="scenario/pricing-discount-order",
        stable=True,
        profiles_dir=profiles_dir,
    )
    second = export_demo(
        profile_name="little_bytes",
        base="main",
        head="scenario/pricing-discount-order",
        stable=True,
        profiles_dir=profiles_dir,
    )

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_demo_validation_rejects_absolute_paths(tmp_path, isolated_kb):
    repo = init_demo_repo(tmp_path)
    profiles_dir = make_profiles_dir(tmp_path, repo)
    artifact = export_demo(
        profile_name="little_bytes",
        base="main",
        head="scenario/pricing-discount-order",
        stable=True,
        profiles_dir=profiles_dir,
    )
    artifact["evidence"]["gap_path"] = "/Users/haleyparks/private.py"

    with pytest.raises(DemoExportError, match="repository-relative"):
        validate_demo_artifact(artifact)


def test_demo_export_fails_clearly_without_gap_evidence(tmp_path, isolated_kb):
    repo = init_demo_repo(tmp_path, missing_lines=[])
    profiles_dir = make_profiles_dir(tmp_path, repo)

    with pytest.raises(DemoExportError, match="no routed gap evidence"):
        export_demo(
            profile_name="little_bytes",
            base="main",
            head="scenario/pricing-discount-order",
            stable=True,
            profiles_dir=profiles_dir,
        )


def test_export_demo_cli_writes_valid_artifact(tmp_path, isolated_kb):
    repo = init_demo_repo(tmp_path)
    output = tmp_path / "demo.json"
    env = {
        **os.environ,
        "QA_KB_PATH": str(isolated_kb),
        "QA_PYTHON": shlex.quote(sys.executable),
        "QA_TARGET_REPO_ROOT": str(repo),
        "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
    }

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "qa_agents",
            "export-demo",
            "--profile",
            "little_bytes",
            "--base",
            "main",
            "--head",
            "scenario/pricing-discount-order",
            "--output",
            str(output),
            "--stable",
        ],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    artifact = json.loads(output.read_text(encoding="utf-8"))
    validate_demo_artifact(artifact)
    assert artifact["change"]["files"] == ["backend/app/pricing.py"]
