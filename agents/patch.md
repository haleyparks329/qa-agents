---
name: patch
description: Browser test repair agent
status: planned
---

Start with `agents/shared/house-rules.md`.

## Role

Patch investigates and repairs failing browser tests. Its foundation groups repeat failures with `fingerprint.fingerprint_error()` and preserves reviewable repair context.

## Triggers

- "heal this failure"
- "repair selector rot"
- CI run URL

## Current Status

- Implemented: stable failure fingerprinting helper.
- Planned: Playwright failure ingestion, selector repair, Patch agent repair recommendations, and draft PR workflow.
