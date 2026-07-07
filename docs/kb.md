# Knowledge Base

The SQLite KB is the local state store for agent runs, observations, patches, bug suspects, and structured gap records.

## Implemented

- Schema migrations in `schema/`.
- `QA_KB_PATH` override.
- Default path: `~/.agents-state/qa.db`.
- Gap record insertion through helpers.
- Query surfaces for gaps, handoff debt, recurrences, abstentions, blocks, and pending patches.
- Advisory gap routing.

## Commands

```bash
python3 kb.py migrate
python3 kb.py stats
python3 kb.py query gaps
python3 kb.py route-gaps
```

## Exit States

Agent runs use:

- `acted`
- `blocked`
- `abstained`

The current repo defines the schema and query surfaces. Full agent run orchestration is planned.
