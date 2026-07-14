import json
import subprocess
import sys


def test_profile_cli_agent_context():
    result = subprocess.run(
        [sys.executable, "profile.py", "--profile", "ecommerce", "agent-context", "beacon"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["agent"] == "beacon"
    assert payload["profile"] == "ecommerce"
    assert payload["test_layout"]["unit_or_integration"] == "tests"


def test_profile_cli_validate():
    result = subprocess.run(
        [sys.executable, "profile.py", "--profile", "saas_dashboard", "validate"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "saas_dashboard is valid" in result.stdout
