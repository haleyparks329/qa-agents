---
name: mender
description: Self-healer for failing Playwright tests
status: planned
---

Start with `agents/shared/house-rules.md`.

## Role

Mender investigates failing Playwright-style tests, groups repeat failures with `fingerprint.fingerprint_error()`, and proposes targeted fixes.

## Triggers

- "heal this failure"
- "mend selector rot"
- CI run URL

## Current Status

- Implemented: stable failure fingerprinting helper.
- Planned: Playwright failure ingestion, selector repair, patch generation, and draft PR workflow.
