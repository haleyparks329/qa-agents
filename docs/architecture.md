# Architecture

`qa-agents` is organized as a small QA agent operating system plus local state.
The deterministic planner is a prototype slice inside that system, not the
system itself.

## Implemented Foundations

```text
agents/
  shared/
    core-rules.md
    house-rules.md
  beacon.md
  patch.md
  lookout.md
  scribe.md
  inspector.md

profiles/
  ecommerce/
    profile.json
    house-rules.md
  saas_dashboard/
    profile.json
    house-rules.md

schema/
  000_init.sql
  001_digest.sql
  002_perf_and_tracker.sql
  003_ticket_id_compat.sql
  004_gap_records.sql

qa_agents/
  kb.py
  profile_config.py
  fingerprint.py
  gap_detector.py
  cli.py
  generator.py
  parser.py
  profiles.py
  renderer.py
```

## Core Data Flow

```text
active profile
        |
        v
agent startup context
        |
        v
agent spec + shared rules
        |
        v
KB state: runs, observations, bugs, patches, gaps
        |
        v
explicit outcome: acted / blocked / abstained
```

## Gap Flow

```text
git diff / coverage JSON / mutation JSON
        |
        v
gap_detector.py
        |
        v
gap_records in SQLite
        |
        v
kb.py route-gaps
        |
        v
recommended agent + reason
```

Routing is advisory. It records where a gap should probably go, but it does not
dispatch work.

## Prototype Slice

```text
simulated feature request
        |
        v
profile-aware Beacon prototype
        |
        v
Markdown QA plan
```

This path is useful because it is runnable and testable, but it is deliberately
small. It does not inspect a real app, heal tests, open PRs, or orchestrate the
other agents.

## Planned Workflows

- Dashboard or tracker over KB state.
- Digest workflow for open attention items.
- Patch selector healing.
- Lookout browser probing.
- Scribe repo-aware test authoring.
- Inspector drift review.
- Agent handoff execution.
