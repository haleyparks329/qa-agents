from qa_agents.strategies import load_behavior, load_strategy, run_investigation


FIXTURE = "strategies/meticulous/fixtures/pricing-change.input.json"


def test_policy_holds_for_confirmed_regression_and_reports_coverage_gap():
    investigation = run_investigation("meticulous", FIXTURE)

    assert investigation["policy_decision"]["decision"] == "hold"
    assert investigation["policy_decision"]["matched_rule"] == "confirmed-functional-regression"
    assert investigation["summary"]["recommendation"] == "hold"
    assert investigation["summary"]["affected_workflows"] == 3
    assert investigation["summary"]["confirmed_regressions"] == 1
    assert investigation["summary"]["expected_changes"] == 1
    assert investigation["coverage_audit"]["coverage_risk"] == "medium"
    assert investigation["coverage_audit"]["uncovered_changed_branches"] == [
        "branch-legacy-coupon-prorated-upgrade"
    ]
    assert investigation["coverage_audit"]["missing_workflows"] == [
        "legacy coupon plus prorated annual upgrade"
    ]


def test_strategy_policy_drives_classification_and_summary_actions():
    strategy = load_strategy("meticulous")
    behavior = load_behavior(strategy)
    investigation = run_investigation("meticulous", FIXTURE)

    assert [rule.classification for rule in behavior.classification_rules] == [
        "expected_change",
        "confirmed_regression",
    ]
    assert behavior.summary_next_actions == investigation["summary"]["next_actions"]
