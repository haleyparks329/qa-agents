---
name: quill
description: Test author
status: prototype
---

Start with `agents/shared/house-rules.md`.

## Role

Quill writes tests from a spec, bug, or structured coverage gap.

## Triggers

- "write regression test for"
- "author test for"
- "fill coverage gap"

## Current Status

- Implemented: advisory routing from `missing_unit_test` and `surviving_mutant` gap records to Quill.
- Prototype: optional Playwright-style stubs from the CLI planner.
- Planned: repo-aware test authoring.
