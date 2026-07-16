from qa_agents.strategies import load_evidence, validate_replay_evidence


FIXTURE = "strategies/meticulous/fixtures/pricing-change.input.json"


def test_pricing_fixture_is_valid_simulated_replay_evidence():
    evidence = load_evidence(FIXTURE)

    assert validate_replay_evidence(evidence, "meticulous") == []
    assert evidence["source"]["simulated"] is True
    assert evidence["source"]["type"] == "simulated_replay_platform"
    assert evidence["replay_summary"]["sessions_affected"] == 17
    assert len(evidence["sessions"]) == 17
    assert all(
        diff["deterministic"] is True
        for session in evidence["sessions"]
        for diff in session["differences"]
    )
