from qa_agents.strategies import cluster_workflows, load_evidence, run_investigation


FIXTURE = "strategies/meticulous/fixtures/pricing-change.input.json"


def test_affected_sessions_cluster_into_three_workflows():
    evidence = load_evidence(FIXTURE)

    clusters = cluster_workflows(evidence)

    assert len(clusters) == 3
    assert sorted(len(cluster.session_ids) for cluster in clusters) == [2, 7, 8]
    assert sum(len(cluster.session_ids) for cluster in clusters) == 17
    assert all(cluster.evidence_refs == cluster.session_ids for cluster in clusters)


def test_investigation_preserves_evidence_refs_for_findings():
    investigation = run_investigation("meticulous", FIXTURE)

    regression = [
        finding
        for finding in investigation["findings"]
        if finding["classification"] == "confirmed_regression"
    ]
    expected = [
        finding
        for finding in investigation["findings"]
        if finding["classification"] == "expected_change"
    ]

    assert len(regression) == 1
    assert regression[0]["session_ids"] == ["session-001", "session-002"]
    assert regression[0]["diff_ids"] == ["diff-001", "diff-002"]
    assert regression[0]["branch_ids"] == ["branch-annual-rounding-total"]
    assert len(expected) == 1
    assert len(expected[0]["session_ids"]) == 15
    assert len(expected[0]["diff_ids"]) == 15
    assert expected[0]["branch_ids"] == ["branch-annual-discount-label"]
