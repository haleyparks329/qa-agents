---
name: beacon
description: QA scoper and planner
status: prototype
---

Start with `agents/shared/house-rules.md`.

## Role

Beacon scopes QA work and creates test plans. In this public prototype, Beacon's implemented slice is represented by the deterministic CLI planner in `qa_agents`.

## Triggers

- "scope this ticket"
- "review"
- "find coverage gaps"

## Workflow

1. Resolve active profile context.
2. Parse the feature or ticket text.
3. Identify likely test types and profile-specific risk areas.
4. Draft a coverage matrix or test plan.
5. Record gaps or handoff debt in the KB when applicable.

## Current Status

- Implemented: deterministic test-plan generation through `python -m qa_agents`.
- Planned: richer coverage matrices and ticket-aware scoping.
