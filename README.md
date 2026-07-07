# QA Agents

A prototype QA agent system that gives specialized agents shared context, memory, and clear responsibilities.

I built this project around a problem I kept seeing in AI-assisted testing: generating tests is easy, but useful QA work depends on context. Different applications have different critical flows, risk areas, constraints, and histories. A checkout flow should not be reasoned about the same way as an analytics dashboard.

QA Agents explores a system where agents do not start from a blank prompt. They load an application profile, follow shared rules, inspect persistent QA state, and produce reviewable outputs.

## The idea

The system is organized around five QA roles:

| Agent | Responsibility | Current status |
|---|---|---|
| **Herbie** | Scope QA work and create test plans | Runnable prototype |
| **Mender** | Investigate and repair failing browser tests | Agent spec; fingerprinting foundation implemented |
| **Scout** | Explore for bugs and risky behavior | Agent spec |
| **Quill** | Author or update tests from accepted plans | Agent spec; routing target and demo stubs |
| **Auditor** | Review coverage gaps and system behavior | Agent spec; KB query foundations |

The larger design connects these roles through shared application context and a local knowledge base:

```text
software change
      ↓
application profile + shared rules
      ↓
specialized QA roles
      ↓
plans · gaps · observations · patches · fingerprints
      ↓
SQLite knowledge base
      ↓
review · routing · follow-up work
```

The goal is not a fully autonomous testing swarm. It is a QA system that is context-aware, inspectable, and explicit about what happened. Agents can `act`, `block`, or `abstain`, and routing is advisory rather than automatic.

## What is implemented

The current repo contains small, working foundations for the larger architecture:

- deterministic, profile-aware QA plan generation
- reusable `ecommerce` and `saas_dashboard` application profiles
- directory-based profile loading with flat JSON compatibility
- profile inspection and agent-context CLI commands
- SQLite migrations and query commands for QA state
- deterministic gap detection using git changes, coverage JSON, and simple mutation reports
- stable error fingerprinting from normalized error text
- advisory gap routing through deterministic gap-type-to-agent mapping
- automated tests for the implemented foundations

The runnable Herbie-inspired demo takes a simulated feature request and an application profile, then generates a QA plan with test cases, risk notes, automation candidates, and optional Playwright-style stubs.

## Quick start

Requires Python 3.12+.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
.venv/bin/pytest
```

Run the demo:

```bash
python3 -m qa_agents examples/feature_request.md --profile ecommerce --stubs
```

Write the generated plan to a file:

```bash
python3 -m qa_agents examples/feature_request.md \
  --profile ecommerce \
  --stubs \
  --output qa_plan_output.md
```

All demo data is simulated. Playwright-style stubs are illustrative output, not browser execution.

## Profiles

Profiles give the system reusable context about an application. They can describe:

- application purpose
- critical user flows
- risk areas
- testing priorities
- repository test layout
- issue tracker hints
- constraints and house rules

This repo includes two generic examples:

```text
profiles/
├── ecommerce/
│   ├── profile.json
│   └── house-rules.md
└── saas_dashboard/
    ├── profile.json
    └── house-rules.md
```

Inspect the available profiles:

```bash
python3 profile.py list
python3 profile.py --profile ecommerce summary
python3 profile.py --profile ecommerce validate
```

Inspect the context that would be provided to an agent:

```bash
python3 profile.py --profile ecommerce agent-context herbie
```

The active profile resolves from `QA_AGENTS_PROFILE`, then `QA_PROFILE`, then defaults to `ecommerce`.

## Knowledge base

The local SQLite KB provides persistent state for the system architecture. The schema supports records such as agent runs, observations, gaps, patches, bugs, blocked work, and abstentions.

By default, the database lives at:

```text
~/.agents-state/qa.db
```

Initialize and inspect it:

```bash
python3 kb.py migrate
python3 kb.py stats
python3 kb.py query gaps
python3 kb.py route-gaps
```

Available query surfaces include:

```text
gaps
handoff-debt
recurrences
abstentions
blocks
pending-patches
```

Set a custom database path with:

```bash
export QA_KB_PATH=/path/to/qa.db
```

## Gap detection and routing

The gap detector turns simple repository signals into reviewable QA gap records.

```bash
python3 gap_detector.py --base origin/main --head HEAD
```

With coverage data:

```bash
python3 gap_detector.py \
  --base origin/main \
  --head HEAD \
  --coverage coverage.json
```

With coverage, mutation data, and advisory routing:

```bash
python3 gap_detector.py \
  --base origin/main \
  --head HEAD \
  --coverage coverage.json \
  --mutation mutation-report.json \
  --route
```

Current behavior is intentionally narrow: changed Python files can produce unit-test coverage gaps, coverage JSON can narrow those gaps to files with missing lines, and simple mutation reports can produce surviving-mutant gaps. Routing then recommends the relevant agent role without dispatching work automatically.

## Repository structure

```text
agents/                 Agent specs and shared rules
docs/                   Architecture, agent, profile, KB, and demo docs
examples/               Simulated demo inputs
profiles/               Generic application profiles
schema/                 SQLite migrations
qa_agents/              Python package implementation
tests/                  Unit and CLI tests

profile.py              Profile inspection CLI
kb.py                   SQLite KB CLI
gap_detector.py         Gap detection CLI
fingerprint.py          Error fingerprint compatibility import
```

## Current scope and roadmap

**Working now:** profile-aware planning, profile resolution, KB migrations and queries, gap detection, error fingerprinting, advisory routing, and tests.

**Prototype slices:** Herbie-inspired planning, illustrative Playwright-style stubs, deterministic agent-role recommendations, and CLI-based KB inspection.

**Planned:** Playwright healing for Mender, browser probing for Scout, repo-aware test writing for Quill, coverage review loops for Auditor, richer orchestration, dashboard and digest surfaces, and draft PR creation.

Planned features are not presented as implemented.

## Design principles

- Context first, generation second.
- Give agents narrow responsibilities.
- Make shared rules explicit.
- Keep memory inspectable.
- Prefer advisory routing until automation is proven.
- Treat `blocked` and `abstained` as valid outcomes.
- Keep demos honest and clearly simulated.

## Project status

This is an early public prototype of a larger QA agent architecture. The most important part of the project is the system shape: specialized roles, reusable context, persistent state, deterministic signals, and reviewable routing.

The implementation is intentionally small enough to inspect and run, while leaving room to grow the individual agents into more capable QA workflows.
