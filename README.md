# qa-agents

`qa-agents` is public-safe QA agent infrastructure for scoping, auditing, gap detection, and test-plan authoring across software repos.

The current repo is intentionally local-first and deterministic. It preserves the original multi-agent architecture, but only implements the narrow foundations that can be tested honestly without private data, paid APIs, or a real production app.

All demo inputs are simulated. Profiles are generic app categories, not company-specific configurations.

## Implemented

- Python package and CLI demo: `python -m qa_agents ...`
- Deterministic profile-aware test-plan generation
- Generic profiles:
  - `ecommerce`
  - `saas_dashboard`
- Agent specs in `agents/`:
  - Herbie: QA scoper and planner
  - Mender: Playwright healer, planned beyond fingerprinting
  - Scout: exploratory bug-hunter, planned
  - Quill: test author, prototype routing target
  - Auditor: QA-for-QA reviewer, prototype KB queries
- Shared agent rules in `agents/shared/`
- Directory-based profile structure with `profile.json` and `house-rules.md`
- `profile.py` CLI for profile inspection and agent context
- SQLite KB migrations and helper CLI:
  - `python3 kb.py migrate`
  - `python3 kb.py stats`
  - `python3 kb.py query gaps`
  - `python3 kb.py route-gaps`
- Stable error fingerprinting helper
- Narrow deterministic gap detector:
  - changed Python files
  - coverage.py JSON missing lines
  - simple mutation-report JSON survivors
  - advisory routing, not auto-dispatch
- Tests for the implemented foundations

## Prototype

- The CLI planner acts as Herbie's first public slice: it turns a simulated feature request and profile into a test plan.
- Optional Playwright-style stubs are generic placeholders for Quill-style test authoring.
- Gap routing recommends an agent, but it does not start that agent.
- KB queries expose basic review surfaces, but they are not a full dashboard.

## Planned

- Dashboard at `dashboard.py`
- Slack or webhook digest from `digest.py`
- Playwright healing and selector repair in Mender
- Browser probing in Scout
- Repo-aware test authoring in Quill
- Automated orchestration between agents
- Draft PR creation
- Rich tracker integration

These are documented as design direction only unless code and tests exist in this repo.

## Architecture

```text
agents/                 Agent specs and shared rules
profiles/               Generic app profiles and profile rules
schema/                 SQLite migrations
qa_agents/              Python package implementation
examples/               Simulated public demo inputs
tests/                  Unit and CLI tests

profile.py              Active-profile inspection CLI
kb.py                   SQLite KB CLI
gap_detector.py         Deterministic gap detector CLI
fingerprint.py          Compatibility import for error fingerprints
```

The KB file lives outside the repo at `$QA_KB_PATH` or `~/.agents-state/qa.db`.

## Quick Start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

## Demo: Generate A QA Plan

```bash
python -m qa_agents examples/feature_request.md --profile ecommerce
```

Include generic Playwright-style stubs:

```bash
python -m qa_agents examples/feature_request.md --profile ecommerce --stubs
```

Write output to a file:

```bash
python -m qa_agents examples/feature_request.md --profile ecommerce --stubs --output qa_plan_output.md
```

## Profile Commands

```bash
python3 profile.py list
python3 profile.py --profile ecommerce show
python3 profile.py --profile ecommerce summary
python3 profile.py --profile ecommerce validate
python3 profile.py --profile ecommerce agent-context herbie
python3 profile.py --profile ecommerce paths
python3 profile.py --profile ecommerce get issue_tracker.ticket_prefixes
python3 profile.py --profile ecommerce resolve-path test_layout.unit_or_integration
```

Active profile resolution checks `QA_AGENTS_PROFILE`, then `QA_PROFILE`, then defaults to `ecommerce`.

## KB Commands

```bash
python3 kb.py migrate
python3 kb.py stats
python3 kb.py query gaps
python3 kb.py route-gaps
```

Supported query surfaces:

- `gaps`
- `handoff-debt`
- `recurrences`
- `abstentions`
- `blocks`
- `pending-patches`

## Gap Detector

```bash
python3 gap_detector.py --base origin/main --head HEAD
python3 gap_detector.py --base origin/main --head HEAD --coverage coverage.json
python3 gap_detector.py --base origin/main --head HEAD --coverage coverage.json --mutation mutation-report.json --route
```

Current behavior:

- Emits `missing_unit_test` gaps for changed Python files.
- Uses coverage JSON to narrow missing-unit gaps to files with missing lines.
- Emits `surviving_mutant` gaps for loose mutation-report JSON shapes.
- Optionally applies advisory routing with `--route`.

## Agent Startup Pattern

```bash
python3 profile.py --profile ecommerce agent-context herbie
python3 profile.py --profile ecommerce resolve-path test_layout.unit_or_integration
python3 kb.py stats
python3 kb.py query gaps
```

Agents should use profile context and KB state before making recommendations.

## Adding A Profile

1. Create `profiles/<name>/profile.json`.
2. Add `profiles/<name>/house-rules.md`.
3. Keep terminology generic and public-safe.
4. Add test layout, issue tracker, and tool hints as structured JSON when useful.
5. Run `pytest`.

## Guardrails

- Use simulated data only.
- Keep profiles generic.
- Do not include private company names, customer data, secrets, internal URLs, or production metrics.
- Do not claim dashboard, Slack digest, Playwright healing, or orchestration exists until it is implemented and tested.
