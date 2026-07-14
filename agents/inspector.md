---
name: inspector
description: QA review agent
status: prototype
---

Start with `agents/shared/house-rules.md`.

## Role

Inspector reviews coverage gaps and system behavior.

## Triggers

- "audit this week"
- "audit closed bugs since"
- "check handoff_debt"

## Current Status

- Implemented: KB queries for gaps, blocks, abstentions, handoff debt, and pending patches.
- Planned: automated weekly audits and drift detection.
