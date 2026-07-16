# QA Agents

QA agent infrastructure for auditing, probing, scoping, healing, and test
authoring across software repos.

I built this project around a problem I kept seeing in AI-assisted testing:
generating tests is easy, but useful QA work depends on context. Different
applications have different critical flows, risk areas, constraints, and
histories. A checkout flow should not be reasoned about the same way as an
analytics dashboard.

QA Agents explores a local-first agent operating system where agents do not
start from a blank prompt. They load an application profile, follow shared
rules, inspect persistent QA state, and produce reviewable outputs.

The repo is public-safe by design. Included profiles and examples are generic;
they are not private workspace configurations. Planned workflows are marked as
planned until there is code and test coverage in this repo.

## The Idea

The system is organized around five QA roles:

| Agent | Responsibility | Current status |
| --- | --- | --- |
| Beacon | Scope QA work and create test plans | Prototype via deterministic CLI |
| Patch | Investigate and repair failing browser tests | Planned beyond fingerprinting and routing foundations |
| Lookout | Explore for bugs and risky behavior | Planned |
| Scribe | Author or update tests from accepted plans, specs, bugs, or gaps | Prototype via stubs and routing target |
| Inspector | Review coverage gaps and system behavior | Prototype via KB query surfaces |

The larger design connects these roles through shared application context and a
local knowledge base:

```text
software change
      |
      v
application profile + shared rules
      |
      v
specialized QA roles
      |
      v
plans / gaps / observations / patches / fingerprints
      |
      v
SQLite knowledge base
      |
      v
review / routing / follow-up work
```

The goal is not a fully autonomous testing swarm. It is a QA system that is
context-aware, inspectable, and explicit about what happened. Agents can
`act`, `block`, or `abstain`, and routing is advisory rather than automatic.

## Quality Strategies

QA Agents can adapt their evidence model and decision rules to different
software quality environments.

Current strategies:

- Default repository investigation
- Meticulous-inspired deterministic replay investigation

The Meticulous-inspired strategy is a simulated exploration based on public
concepts. It demonstrates how agents can reason over replay evidence without
replacing or weakening the deterministic execution layer.

## Status Summary

### Implemented

- Agent spec files for Beacon, Patch, Lookout, Scribe, and Inspector.
- Shared repo-agnostic agent rules in `agents/shared/`.
- Generic directory-based profiles with `profile.json` and `house-rules.md`.
- Profile inspection CLI through `profile.py`.
- SQLite KB migrations and helpers through `kb.py` / `qa_agents.kb`.
- Explicit KB outcome vocabulary: `acted`, `blocked`, `abstained`.
- Observation query surfaces for blocked runs, abstentions, handoff debt,
  recurrences, pending patches, and open gaps.
- Stable error fingerprinting helper.
- Structured `gap_records` schema and helper functions.
- Narrow deterministic gap detector for changed Python files, coverage.py JSON,
  and simple mutation-report JSON.
- Advisory gap routing with recommended agent and route reason.
- Deterministic evidence runner foundation for profile-configured target repos,
  including command execution records, coverage ingestion, and gap routing.
- Public-safe Beacon prototype CLI for turning a simulated feature request into
  a QA plan.
- Tests for the implemented foundations.

### Prototype

- Beacon: deterministic profile-aware QA plan generation from simulated input.
- Scribe: optional generic Playwright-style stubs from the Beacon prototype and
  advisory routing target for test-authoring gaps.
- Inspector: KB query surfaces that expose gaps, drift signals, blocked work, and
  handoff debt.
- Patch: failure fingerprinting and routing foundations, without automated
  Playwright healing.
- Gap routing: advisory only; it does not auto-dispatch agents.

### Planned

- Live tracker/dashboard over the KB.
- Daily or scheduled digest workflow.
- Automated Patch selector healing for failing Playwright tests.
- Lookout browser probing workflow.
- Scribe repo-aware test authoring from gaps, bugs, or specs.
- Inspector weekly drift review workflow.
- Agent orchestration and handoff execution.
- Draft PR or tracker creation.
- Richer gap types and mutation ingestion.

## Quick Start

Requires Python 3.12+.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
.venv/bin/pytest
```

Run the Beacon prototype:

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

All demo data is simulated. Playwright-style stubs are illustrative output, not
browser execution.

Run the deterministic evidence-loop foundation:

```bash
export QA_TARGET_REPO_ROOT=../little-bytes
python3 -m qa_agents run --profile little_bytes --base main --head HEAD
```

The companion Little Bytes reference repository lives at
`haleyparks329/little-bytes`. Integration tests also exercise this runner with
temporary fixture repositories. The runner executes configured evidence
commands, ingests configured coverage reports, persists normalized execution
records, creates routable gap records, and emits advisory next actions. It does
not generate tests, dispatch agents, open PRs, or use an LLM to interpret raw
command output.

## Real Reference Application

[Little Bytes](https://github.com/haleyparks329/little-bytes) is the controlled
bakery application-under-test for the first real evidence loop. QA Agents runs
against an actual Little Bytes git diff, executes the configured unit test
command, reads the generated coverage report, persists a `missing_unit_test`
gap, and recommends Scribe for human-reviewed regression coverage.

```text
Little Bytes pricing change
-> passing tests
-> uncovered changed behavior
-> missing_unit_test gap
-> Scribe recommendation
```

The canonical public-safe replay artifact is
[`examples/demo-runs/little-bytes-pricing.json`](examples/demo-runs/little-bytes-pricing.json).
It is generated from normalized run evidence and sanitized for docs or website
display. It is not proof that Scribe executed: no tests, patches, PRs, browser
runs, or LLM-authored summaries are generated in this phase.

Regenerate the artifact:

```bash
export QA_TARGET_REPO_ROOT=../little-bytes
export QA_KB_PATH=/tmp/qa-agents-little-bytes-demo.db
rm -f "$QA_KB_PATH"

python3 -m qa_agents export-demo \
  --profile little_bytes \
  --base main \
  --head scenario/pricing-discount-order \
  --output examples/demo-runs/little-bytes-pricing.json \
  --stable
```

## Architecture

```text
agents/
  shared/
    core-rules.md       Repo-agnostic cross-agent context
    house-rules.md      Compatibility entrypoint for shared rules
  beacon.md             QA scoper and planner
  patch.md              Browser test repair agent
  lookout.md            Exploratory QA agent
  scribe.md             Test authoring agent
  inspector.md          QA review agent

profiles/
  ecommerce/
    profile.json        Generic public-safe app profile
    house-rules.md      Profile-specific conventions
  saas_dashboard/
    profile.json        Generic public-safe app profile
    house-rules.md      Profile-specific conventions

schema/
  000_init.sql          Core graph-shaped KB schema
  001_digest.sql        Digest run tracking
  002_perf_and_tracker.sql
  003_ticket_id_compat.sql
  004_gap_records.sql   Structured gap records
  005_execution_records.sql

qa_agents/
  kb.py                 SQLite helpers
  profile_config.py     Active profile context helpers
  fingerprint.py        Stable failure fingerprints
  gap_detector.py       Artifact-driven gap detector
  run.py                Deterministic target-repo evidence runner
  demo_export.py        Public-safe evidence artifact exporter
  cli.py                Small Beacon prototype runner
  generator.py          Prototype QA plan generator
```

Top-level compatibility entrypoints:

```text
profile.py              Active-profile loader / CLI
kb.py                   SQLite KB CLI
gap_detector.py         Gap detector CLI
fingerprint.py          Fingerprint import shim
```

The database file lives outside the repo at `$QA_KB_PATH` or
`~/.agents-state/qa.db`.

## Profiles

Profiles keep app-specific context out of the shared agent specs.

Active profile resolution:

1. `--profile <name>` when a CLI supports it
2. `QA_AGENTS_PROFILE`
3. `QA_PROFILE`
4. default: `ecommerce`

Profile commands:

```bash
python3 profile.py list
python3 profile.py show
python3 profile.py summary
python3 profile.py validate
python3 profile.py agent-context inspector
python3 profile.py repo-root
python3 profile.py repo-name
python3 profile.py tracker
python3 profile.py ticket-prefixes
python3 profile.py paths
python3 profile.py paths e2e unit_or_integration
python3 profile.py tool heal_skill
python3 profile.py get issue_tracker.ticket_prefixes
python3 profile.py resolve-path test_layout.e2e
```

To add a profile:

1. Create `profiles/<name>/profile.json`.
2. Add `profiles/<name>/house-rules.md`.
3. Put target-specific terminology, test layout, tracker rules, and tool hints
   there.
4. Keep `agents/shared/core-rules.md` generic.
5. Prefer machine-readable profile values over prose-only conventions.

## Knowledge Base

The SQLite KB stores local state for agent runs, observations, patches, bug
suspects, and structured gap records.

```bash
python3 kb.py migrate
python3 kb.py stats
python3 kb.py query gaps
python3 kb.py query handoff-debt
python3 kb.py query recurrences
python3 kb.py query abstentions
python3 kb.py query blocks
python3 kb.py query pending-patches
python3 kb.py route-gaps
```

Set a custom database path with:

```bash
export QA_KB_PATH=/path/to/qa.db
```

Every agent run should end in one explicit outcome:

- `acted`: produced a PR, test, doc, draft ticket, or other concrete artifact.
- `blocked`: cannot proceed; records what is needed next.
- `abstained`: chose not to act and records the reason.

Use `observation(kind='handoff_debt')` when an agent does work that should
belong to another agent or future workflow. Those records become prioritization
signals.

## Structured Gap Records

`gap_records` hold typed, routable gaps for detectors and downstream agents.
Narrative context remains in `observations`.

Current v1 support:

- Schema in `schema/004_gap_records.sql`.
- KB helpers in `qa_agents.kb`.
- Deterministic detection in `qa_agents.gap_detector`.
- CLI inspection through `kb.py query gaps`.
- Advisory routing through `kb.py route-gaps`.

Routing is intentionally advisory. It assigns `recommended_agent` and
`route_reason`; it does not start work automatically.

## Gap Detection And Routing

The gap detector turns simple repository signals into reviewable QA gap records.

```bash
python3 gap_detector.py --base origin/main --head HEAD
python3 gap_detector.py --base origin/main --head HEAD --coverage coverage.json
python3 gap_detector.py --base origin/main --head HEAD --coverage coverage.json --mutation mutation-report.json --route
```

Current behavior:

- Emits `missing_unit_test` gaps for changed Python files.
- Uses coverage.py JSON to narrow missing-unit gaps to changed files with
  missing lines.
- Emits `surviving_mutant` gaps for loose mutation-report JSON shapes.
- Skips non-Python files in the current implementation.
- Optionally applies advisory routing after gap creation.

Accepted mutation JSON shapes are intentionally loose in v1:

- Top-level list of mutation objects.
- Object with `mutations`, `results`, or `items` as a list.

Each mutation object should include a file/path field and a status/state/result
field. Surviving states currently recognized: `survived`, `survivor`,
`timeout`, `timed_out`.

## Agent Startup Pattern

Agents should resolve the active profile and inspect KB state before acting.

```bash
python3 profile.py agent-context beacon
python3 profile.py resolve-path test_layout.unit_or_integration
python3 kb.py stats
python3 kb.py query gaps
```

Use `agent-context <agent>` when an agent needs structured startup context. Use
the narrower commands when a shell script only needs one field.

## Beacon Prototype Slice

The deterministic planner is only a runnable prototype slice, not the center of
the repository.

```bash
python3 -m qa_agents examples/feature_request.md --profile ecommerce
python3 -m qa_agents examples/feature_request.md --profile ecommerce --stubs
python3 -m qa_agents examples/feature_request.md --profile ecommerce --stubs --output qa_plan_output.md
```

It uses simulated input and generic profiles to produce a reviewable QA plan.
It does not claim to inspect a real application, run browser tests, create PRs,
or dispatch other agents.

## Repository Structure

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

## Design Principles

- Context first, generation second.
- Give agents narrow responsibilities.
- Make shared rules explicit.
- Keep memory inspectable.
- Prefer advisory routing until automation is proven.
- Treat `blocked` and `abstained` as valid outcomes.
- Keep examples honest and clearly simulated.

## Guardrails

- Keep all examples and profiles generic/public-safe.
- Do not include private company names, customer data, secrets, internal URLs,
  or real production metrics.
- Do not make fake production claims.
- Mark capabilities as implemented, prototype, or planned.
- Keep repo-specific rules in profiles, not shared agent specs.
- Use `fingerprint.fingerprint_error()` for any stored `error_fingerprint`
  value so repeated failures group consistently across agents.
