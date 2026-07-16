import subprocess
import sys
import json


def test_cli_smoke():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "qa_agents",
            "examples/feature_request.md",
            "--profile",
            "ecommerce",
            "--stubs",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "QA Test Plan: Saved Cart Reminder" in result.stdout
    assert "Playwright-Style Stubs" in result.stdout


def test_investigate_cli_with_meticulous_strategy():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "qa_agents",
            "investigate",
            "--strategy",
            "meticulous",
            "--input",
            "strategies/meticulous/fixtures/pricing-change.input.json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    investigation = json.loads(result.stdout)
    assert investigation["policy_decision"]["decision"] == "hold"
    assert investigation["summary"]["affected_workflows"] == 3


def test_investigate_cli_reports_malformed_evidence(tmp_path):
    bad_evidence = tmp_path / "bad-evidence.json"
    bad_evidence.write_text('{"source": [], "sessions": [{}]}', encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "qa_agents",
            "investigate",
            "--strategy",
            "meticulous",
            "--input",
            str(bad_evidence),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Invalid evidence for strategy 'meticulous'" in result.stderr
    assert "source must be an object" in result.stderr
    assert "sessions[0] missing session_id" in result.stderr
