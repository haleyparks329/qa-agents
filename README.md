# qa-agents

`qa-agents` is a small public prototype for profile-aware, AI-assisted QA planning. It takes a simulated feature request plus a reusable QA profile, then produces a deterministic test plan with test cases, classifications, risk notes, automation candidates, and optional Playwright-style stubs.

All examples are simulated. The repo does not contain private company data, production claims, paid API calls, or real customer references.

## Why profiles matter

Most QA planning is context-sensitive. A checkout change and a dashboard export change can both sound simple, but they carry different risks, user flows, and automation priorities.

Profiles keep that context explicit. Instead of baking one app's assumptions into the agent, each profile describes:

- what kind of app is being tested
- which user flows matter most
- where defects are most likely to hurt
- what constraints the QA agent must respect

That makes the planner reusable across generic app types without pretending it knows a specific private codebase.

## How it works

1. A Markdown feature request is parsed into a title, summary, and requirements.
2. A JSON QA profile is loaded from `profiles/`.
3. Deterministic rules classify the likely test type and combine the feature with profile risks.
4. The CLI renders a Markdown test plan.

The current planner is intentionally simple. It is closer to a clear rules-based prototype than an autonomous agent, which makes the behavior easy to inspect and test.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the demo:

```bash
python -m qa_agents examples/feature_request.md --profile ecommerce
```

Include Playwright-style stubs:

```bash
python -m qa_agents examples/feature_request.md --profile ecommerce --stubs
```

Write output to a file:

```bash
python -m qa_agents examples/feature_request.md --profile ecommerce --stubs --output qa_plan_output.md
```

Run tests:

```bash
pytest
```

## Demo

Input:

- `examples/feature_request.md`
- `profiles/ecommerce.json`

Output includes:

- test cases
- test type classification
- risk notes from the selected profile
- automation candidates
- optional Playwright-style stubs

Try the dashboard-oriented profile:

```bash
python -m qa_agents examples/feature_request.md --profile saas_dashboard --stubs
```

## Tech stack

- Python 3.10+
- Standard library JSON, dataclasses, argparse, pathlib
- pytest for tests
- Markdown and JSON for demo inputs

No paid APIs are required.

## Limitations

- Uses deterministic mock logic, not an LLM.
- Does not inspect a real repository or application.
- Does not execute browser tests.
- Playwright-style stubs are intentionally generic placeholders.
- Demo plans are only as good as the profile and feature request inputs.

## Roadmap

- Add richer profile validation.
- Support multiple feature request formats.
- Add structured JSON output beside Markdown.
- Add profile-specific heuristics for more precise classifications.
- Generate fuller Playwright examples from a supplied route map or test fixture.
- Add a small local knowledge base for prior simulated QA findings.

## Guardrails

- Demo data is simulated.
- Profiles are generic, not company-specific.
- No private data belongs in this repo.
- No fake production claims or invented metrics.
