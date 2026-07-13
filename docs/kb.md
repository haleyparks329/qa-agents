# Knowledge Base

The SQLite KB is the local state store for agent runs, observations, patches,
bug suspects, and structured gap records.

## Implemented

- Schema migrations in `schema/`.
- `QA_KB_PATH` override.
- Default path: `~/.agents-state/qa.db`.
- Core tables for runs, observations, bugs, tests, patches, and gaps.
- Query surfaces for gaps, handoff debt, recurrences, abstentions, blocks, and
  pending patches.
- Advisory gap routing.

## Commands

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

## Exit States

Agent runs use:

- `acted`
- `blocked`
- `abstained`

The current repo defines the schema, helper functions, and query surfaces. Full
agent run orchestration is planned.

## Gap Records

`gap_records` are structured and routable. They are for detectors and agents.
`observations` remain the human narrative log.

Current routing is advisory only: it writes `recommended_agent` and
`route_reason`, then stops.
