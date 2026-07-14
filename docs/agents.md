# Agents

The repo keeps one markdown spec per specialized agent. Shared behavior belongs
in `agents/shared/`; profile-specific behavior belongs in `profiles/`.

## Status

| Agent | Responsibility | Current status |
| --- | --- | --- |
| Beacon | Scope QA work and create test plans | Prototype via deterministic CLI |
| Patch | Investigate and repair failing browser tests | Planned beyond fingerprinting and routing foundations |
| Lookout | Explore for bugs and risky behavior | Planned |
| Scribe | Author or update tests from accepted plans, specs, bugs, or gaps | Prototype via stubs and routing target |
| Inspector | Review coverage gaps and system behavior | Prototype via KB query surfaces |

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
python3 profile.py --profile ecommerce agent-context beacon
python3 profile.py --profile ecommerce resolve-path test_layout.unit_or_integration
python3 kb.py stats
python3 kb.py query gaps
```

The current implementation provides the shared files, profile context, KB
surfaces, fingerprints, and the Beacon prototype. Full autonomous agent
execution is planned.
