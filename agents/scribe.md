---
name: scribe
description: Test authoring agent
status: prototype
---

Start with `agents/shared/house-rules.md`.

## Role

Scribe authors or updates tests from accepted plans, specifications, bugs, or gaps.

## Triggers

- "write regression test for"
- "author test for"
- "fill coverage gap"

## Current Status

- Implemented: advisory routing from `missing_unit_test` and `surviving_mutant` gap records to Scribe.
- Prototype: optional Playwright-style stubs from the CLI planner.
- Planned: repo-aware test authoring.
