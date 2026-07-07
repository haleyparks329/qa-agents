from __future__ import annotations

from .models import TestPlan


def render_markdown(plan: TestPlan) -> str:
    lines: list[str] = [
        f"# QA Test Plan: {plan.feature.title}",
        "",
        "> Demo data only. This output is generated from a simulated feature request and a generic QA profile.",
        "",
        "## Selected Profile",
        "",
        f"- **Profile:** `{plan.profile.name}`",
        f"- **App context:** {plan.profile.app_description}",
        "",
        "## Parsed Feature",
        "",
        f"- **Summary:** {plan.feature.summary}",
    ]

    if plan.feature.requirements:
        lines.extend(["- **Requirements:**"])
        lines.extend(f"  - {item}" for item in plan.feature.requirements)

    lines.extend(["", "## Test Cases", ""])
    for index, case in enumerate(plan.test_cases, start=1):
        lines.extend(
            [
                f"### {index}. {case.title}",
                "",
                f"- **Type:** {case.test_type}",
                f"- **Automation candidate:** {'yes' if case.automation_candidate else 'not yet'}",
                f"- **Risk note:** {case.risk_note}",
                "- **Steps:**",
            ]
        )
        lines.extend(f"  {step_index}. {step}" for step_index, step in enumerate(case.steps, start=1))
        lines.extend([f"- **Expected result:** {case.expected_result}", ""])

    lines.extend(["## Risk Notes", ""])
    lines.extend(f"- {note}" for note in plan.risk_notes)

    lines.extend(["", "## Automation Candidates", ""])
    if plan.automation_candidates:
        lines.extend(f"- {candidate}" for candidate in plan.automation_candidates)
    else:
        lines.append("- No strong automation candidates identified.")

    if plan.playwright_stubs:
        lines.extend(["", "## Playwright-Style Stubs", ""])
        for stub in plan.playwright_stubs:
            lines.extend(["```ts", stub, "```", ""])

    return "\n".join(lines).rstrip() + "\n"
