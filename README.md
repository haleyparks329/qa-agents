# QA Agents

A local-first QA agent system for turning messy software changes into clearer testing work.

The project explores a simple idea: QA agents should not behave like generic test generators. They should understand the application context, follow shared rules, remember what happened before, and know when to act, abstain, or ask for help.

This repo is public-safe and uses only simulated examples. It does not contain private company data, production metrics, internal URLs, or customer information.

## What This Is

`qa-agents` is a prototype QA agent operating system.

It combines:

- named QA agents with different responsibilities
- reusable app profiles that provide context
- shared rules for how agents should behave
- a small SQLite knowledge base for runs, gaps, patches, and observations
- deterministic gap detection and failure fingerprinting
- a runnable Herbie prototype that generates profile-aware QA plans

The goal is not to build a magic autonomous QA swarm. The goal is to make QA work more structured, reviewable, and context-aware.

## Why I Built This

A lot of AI testing tools start from the same place:

> Here is a feature. Generate tests.

That is useful, but it misses the part that usually makes QA hard.

Different applications have different risks. A checkout flow, an analytics dashboard, and an internal admin tool should not be tested the same way. A good QA system needs context: important flows, known risk areas, test layout, house rules, and what has broken before.

This project treats that context as part of the system.

Profiles give agents reusable knowledge about the app. The KB gives them memory. Agent specs give them clear roles. Gap detection gives them signals. Routing gives the system a way to suggest who should look next without pretending everything should be automated.

## System Model

```text
software change
      |
      v
profile context + shared rules
      |
      v
QA agents
      |
      v
plans, gaps, observations, patches, fingerprints
      |
      v
SQLite KB
      |
      v
review, routing, follow-up work
```

The current implementation is intentionally small. It implements the foundations that can be tested honestly in a public repo.

## Agents

The original system design uses five agents:

| Agent | Role | Current status |
|---|---|---|
| Herbie | Scopes QA work and creates test plans | Prototype implemented through the CLI planner |
| Mender | Investigates and repairs failing Playwright-style tests | Spec only; fingerprinting foundation exists |
| Scout | Looks for exploratory bugs and risky behavior | Spec only |
| Quill | Authors or updates tests from accepted plans | Spec plus deterministic routing target; demo stubs only |
| Auditor | Reviews QA coverage and agent behavior | Spec plus basic KB query surfaces |

Agents share the same rules:

- use the active profile before making recommendations
- check KB state where relevant
- keep outputs reviewable
- prefer advisory routing over automatic dispatch
- clearly report whether they acted, blocked, or abstained

## Profiles

Profiles are reusable QA context for an application or environment.

A profile can describe:

- what the app does
- important user flows
- risk areas
- testing priorities
- test layout
- issue tracker hints
- house rules
- constraints agents should respect

This repo includes two simulated profiles:

```text
profiles/ecommerce/
profiles/saas_dashboard/
```

The older flat JSON profile format is still supported for compatibility.

## Knowledge Base

The KB is a local SQLite database used to track QA system state.

It can store records such as:

- agent runs
- observations
- gaps
- patches
- repeated failure fingerprints
- blocked or abstained work

By default, the DB lives outside the repo:

```text
~/.agents-state/qa.db
```

You can override it with:

```bash
export QA_KB_PATH=/path/to/qa.db
```

## What Works Today

Implemented:

- Python package and CLI
- deterministic, profile-aware QA plan generation
- generic `ecommerce` and `saas_dashboard` profiles
- directory-based profile loading
- flat JSON profile compatibility
- profile inspection CLI
- SQLite schema migration
- basic KB stats and SQL-backed query commands
- deterministic gap detection for changed Python files, coverage JSON, and simple mutation-report JSON
- stable error fingerprinting through normalized error text
- advisory gap routing through deterministic gap-type-to-agent mapping
- tests for the implemented foundations

Prototype slices:

- Herbie-inspired QA planning from a simulated feature request and application profile
- Playwright-style test stubs as illustrative demo output only
- deterministic recommendations that map detected gap types to the appropriate agent role
- SQLite query commands for inspecting gaps, recurrences, blocked work, abstentions, and pending patches

Planned:

- Mender Playwright healing
- Scout browser probing
- Quill repo-aware test writing
- Auditor coverage review loops
- dashboard
- digest/webhook summaries
- automated orchestration
- draft PR creation

Planned means planned. It is not claimed as working unless there is code and test coverage in this repo.

## Quick Start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
.venv/bin/pytest
```

## Run The Demo

Generate a QA plan for a simulated ecommerce feature request:

```bash
python3 -m qa_agents examples/feature_request.md --profile ecommerce
```

Include generic Playwright-style stubs:

```bash
python3 -m qa_agents examples/feature_request.md --profile ecommerce --stubs
```

Write the output to a file:

```bash
python3 -m qa_agents examples/feature_request.md --profile ecommerce --stubs --output qa_plan_output.md
```

The demo data is simulated. The stubs are examples, not proof of browser execution.

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

Active profile resolution checks:

1. `QA_AGENTS_PROFILE`
2. `QA_PROFILE`
3. default: `ecommerce`

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

## Gap Detection

```bash
python3 gap_detector.py --base origin/main --head HEAD
python3 gap_detector.py --base origin/main --head HEAD --coverage coverage.json
python3 gap_detector.py --base origin/main --head HEAD --coverage coverage.json --mutation mutation-report.json --route
```

Current behavior:

- emits `missing_unit_test` gaps for changed Python files
- uses coverage JSON to narrow missing-unit gaps to files with missing lines
- emits `surviving_mutant` gaps from simple mutation-report JSON
- optionally applies advisory routing with `--route`

Routing is advisory. It recommends the next agent surface; it does not automatically dispatch work.

## Repository Layout

```text
agents/                 Agent specs and shared rules
docs/                   Architecture, agents, profiles, KB, demo notes
examples/               Simulated public demo inputs
profiles/               Generic app profiles and profile rules
schema/                 SQLite migrations
qa_agents/              Python package implementation
tests/                  Unit and CLI tests

profile.py              Active-profile inspection CLI
kb.py                   SQLite KB CLI
gap_detector.py         Deterministic gap detector CLI
fingerprint.py          Compatibility import for error fingerprints
```

## Agent Startup Pattern

A future agent should start by loading context rather than guessing:

```bash
python3 profile.py --profile ecommerce agent-context herbie
python3 profile.py --profile ecommerce resolve-path test_layout.unit_or_integration
python3 kb.py stats
python3 kb.py query gaps
```

The point is to make the agent's behavior traceable: which profile it used, what state it checked, what it decided, and whether it acted, blocked, or abstained.

## Adding A Profile

1. Create `profiles/<name>/profile.json`.
2. Add `profiles/<name>/house-rules.md`.
3. Keep terminology generic and public-safe.
4. Add test layout, issue tracker, and tool hints as structured JSON when useful.
5. Run `.venv/bin/pytest`.

## Design Principles

- Context first, generation second.
- Agents should have narrow roles.
- Shared rules matter more than clever prompts.
- Memory should be explicit and inspectable.
- Routing should be advisory until automation is proven.
- `blocked` and `abstained` are valid outcomes.
- Simulated demos should be clearly labeled.

## Guardrails

- Use simulated data only.
- Keep profiles generic.
- Do not include private company names, customer data, secrets, internal URLs, or production metrics.
- Do not claim dashboard, digest, healing, browser probing, or orchestration exists until it is implemented and tested.

## Project Status

This is an early public prototype of a larger QA agent architecture.

The useful part is not that it can print a test plan. The useful part is the system shape: profiles, agents, rules, KB state, gap signals, fingerprints, and reviewable routing.

That is the part this repo is meant to explore.
