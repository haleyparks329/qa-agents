import subprocess
import sys


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
