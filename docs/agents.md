# Agents

The repo keeps one markdown spec per specialized agent. Shared behavior belongs
in `agents/shared/`; profile-specific behavior belongs in `profiles/`.

## Status

| Agent | Role | Current status |
| --- | --- | --- |
| Herbie | Scope tickets, draft coverage matrices, draft regression tests | Prototype through deterministic CLI |
| Mender | Heal failing browser tests | Planned beyond fingerprinting and advisory routing |
| Scout | Probe targets adversarially | Planned |
| Quill | Write tests from specs, bugs, or gaps | Prototype through stubs and routing target |
| Auditor | Verify shipped work and find drift | Prototype through KB query surfaces |

## Shared Contract

Every agent should:

- Load shared rules from `agents/shared/house-rules.md`.
- Resolve active profile context before making recommendations.
- Inspect relevant KB state when previous runs or gaps matter.
- Use stable fingerprints for repeated failures.
- End with `acted`, `blocked`, or `abstained`.
- Record handoff debt when the right owner is another agent or future workflow.

## Startup Pattern

```bash
python3 profile.py --profile ecommerce agent-context herbie
python3 profile.py --profile ecommerce resolve-path test_layout.unit_or_integration
python3 kb.py stats
python3 kb.py query gaps
```

The current implementation provides the shared files, profile context, KB
surfaces, fingerprints, and the Herbie prototype. Full autonomous agent
execution is planned.
