from __future__ import annotations

import re

from .models import FeatureRequest, QAProfile, TestCase, TestPlan


KEYWORD_TYPES = {
    "payment": "integration",
    "checkout": "end-to-end",
    "cart": "end-to-end",
    "login": "end-to-end",
    "auth": "security",
    "permission": "security",
    "role": "security",
    "export": "integration",
    "report": "functional",
    "filter": "functional",
    "dashboard": "visual",
    "notification": "integration",
    "email": "integration",
    "mobile": "responsive",
    "latency": "performance",
}


def generate_test_plan(
    feature: FeatureRequest,
    profile: QAProfile,
    include_playwright_stubs: bool = False,
) -> TestPlan:
    source_text = " ".join([feature.title, feature.summary, *feature.requirements]).lower()
    matched_type = _classify(source_text)
    test_cases = _base_cases(feature, profile, matched_type)
    risk_notes = _risk_notes(feature, profile, source_text)
    automation_candidates = [
        case.title for case in test_cases if case.automation_candidate
    ]
    playwright_stubs = (
        [_playwright_stub(case, profile) for case in test_cases if case.automation_candidate]
        if include_playwright_stubs
        else []
    )

    return TestPlan(
        feature=feature,
        profile=profile,
        test_cases=test_cases,
        risk_notes=risk_notes,
        automation_candidates=automation_candidates,
        playwright_stubs=playwright_stubs,
    )


def _classify(text: str) -> str:
    for keyword, test_type in KEYWORD_TYPES.items():
        if keyword in text:
            return test_type
    return "functional"


def _base_cases(feature: FeatureRequest, profile: QAProfile, matched_type: str) -> list[TestCase]:
    primary_flow = profile.key_user_flows[0]
    secondary_flow = profile.key_user_flows[1] if len(profile.key_user_flows) > 1 else primary_flow
    primary_risk = profile.risk_areas[0]
    secondary_risk = profile.risk_areas[1] if len(profile.risk_areas) > 1 else primary_risk
    requirement = (feature.requirements[0] if feature.requirements else feature.summary).rstrip(".")

    return [
        TestCase(
            title=f"Happy path: {feature.title}",
            test_type=matched_type,
            steps=[
                f"Start from the simulated {profile.name} app baseline.",
                f"Navigate through: {primary_flow}.",
                f"Exercise the requested behavior: {requirement}.",
                "Confirm the user-visible result is clear and reversible where applicable.",
            ],
            expected_result="The feature completes successfully and preserves existing flow behavior.",
            risk_note=f"Watch for regressions around {primary_risk}.",
            automation_candidate=True,
        ),
        TestCase(
            title=f"Boundary and validation coverage for {feature.title}",
            test_type="negative",
            steps=[
                "Try missing, malformed, duplicated, or out-of-range simulated inputs.",
                f"Repeat the flow through: {secondary_flow}.",
                "Check that the UI gives recoverable feedback without losing state.",
            ],
            expected_result="Invalid input is blocked or explained without corrupting simulated data.",
            risk_note=f"Likely failure area: {secondary_risk}.",
            automation_candidate=True,
        ),
        TestCase(
            title=f"Regression check against profile priorities",
            test_type="regression",
            steps=[
                "Run the highest-priority existing flow from the selected profile.",
                "Compare visible behavior before and after the simulated feature change.",
                "Confirm no unrelated profile constraint is violated.",
            ],
            expected_result="Existing priority flows still behave as expected.",
            risk_note=f"Profile priority to protect: {profile.test_priorities[0]}.",
            automation_candidate=False,
        ),
    ]


def _risk_notes(feature: FeatureRequest, profile: QAProfile, source_text: str) -> list[str]:
    notes = [
        f"Profile risk: {risk_area}." for risk_area in profile.risk_areas[:3]
    ]
    for constraint in profile.constraints[:2]:
        notes.append(f"Constraint to respect: {constraint}.")
    if "simulated" not in source_text:
        notes.append("Prototype note: this plan uses simulated data only; no real app inspection is assumed.")
    if feature.requirements:
        notes.append(f"Requirement count parsed from input: {len(feature.requirements)}.")
    return notes


def _playwright_stub(case: TestCase, profile: QAProfile) -> str:
    slug = re.sub(r"[^a-z0-9]+", " ", case.title.lower()).strip().replace(" ", " ")
    test_name = slug[:80]
    return (
        "test('{name}', async ({{ page }}) => {{\n"
        "  await page.goto('/');\n"
        "  await page.getByRole('button', {{ name: /start|continue|save/i }}).first().click();\n"
        "  await expect(page.getByText(/{profile}/i)).toBeVisible();\n"
        "  // Replace selectors with app-specific locators when applying this stub.\n"
        "}});"
    ).format(name=test_name, profile=re.escape(profile.name.replace("_", " ")))
