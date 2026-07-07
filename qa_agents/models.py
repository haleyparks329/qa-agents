from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class QAProfile:
    name: str
    app_description: str
    key_user_flows: list[str]
    risk_areas: list[str]
    test_priorities: list[str]
    constraints: list[str]


@dataclass(frozen=True)
class FeatureRequest:
    title: str
    summary: str
    requirements: list[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass(frozen=True)
class TestCase:
    title: str
    test_type: str
    steps: list[str]
    expected_result: str
    risk_note: str
    automation_candidate: bool


@dataclass(frozen=True)
class TestPlan:
    feature: FeatureRequest
    profile: QAProfile
    test_cases: list[TestCase]
    risk_notes: list[str]
    automation_candidates: list[str]
    playwright_stubs: list[str]
