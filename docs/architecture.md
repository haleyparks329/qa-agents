# Architecture

`qa-agents` is organized around a small agent system plus local state.

## Implemented

```text
agents/
  shared/
    core-rules.md
    house-rules.md
  herbie.md
  mender.md
  scout.md
  quill.md
  auditor.md

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
  cli.py
  generator.py
  parser.py
  profiles.py
  profile_config.py
  kb.py
  gap_detector.py
  fingerprint.py
```

The current CLI planner follows this path:

```text
Markdown feature request
        |
        v
FeatureRequest
        |
        v
active QA profile
        |
        v
deterministic planner
        |
        v
Markdown test plan
```

The KB/gap-detector path is separate:

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

## Prototype

- Herbie is represented by deterministic test-plan generation.
- Quill is represented by generic Playwright-style stubs and advisory routing targets.
- Auditor is represented by KB query surfaces.
- Mender has only the fingerprinting foundation.

## Planned

- Dashboard UI.
- Slack or webhook digest.
- Playwright failure healing.
- Browser probing.
- Automated agent orchestration.
- Draft PR creation.
