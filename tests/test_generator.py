from qa_agents.generator import generate_test_plan
from qa_agents.parser import parse_feature_request
from qa_agents.profiles import load_profile


def test_generates_test_plan_with_profile_risks():
    feature = parse_feature_request("examples/feature_request.md")
    profile = load_profile("ecommerce")

    plan = generate_test_plan(feature, profile, include_playwright_stubs=True)

    assert len(plan.test_cases) == 3
    assert plan.test_cases[0].test_type == "end-to-end"
    assert plan.automation_candidates
    assert plan.playwright_stubs
    assert any("Profile risk" in note for note in plan.risk_notes)
