# Agents

The repo keeps one markdown spec per agent.

## Implemented / Prototype / Planned

| Agent | Role | Current status |
| --- | --- | --- |
| Herbie | Scope tickets, draft coverage matrices, draft regression tests | Prototype through deterministic CLI planner |
| Mender | Heal failing Playwright tests | Planned beyond fingerprinting |
| Scout | Probe targets adversarially | Planned |
| Quill | Write tests from specs, bugs, or gaps | Prototype through stubs and routing target |
| Auditor | Verify shipped work and find drift | Prototype through KB query surfaces |

## Startup Pattern

```bash
python3 profile.py --profile ecommerce agent-context herbie
python3 profile.py --profile ecommerce resolve-path test_layout.unit_or_integration
python3 kb.py stats
python3 kb.py query gaps
```

Agents should resolve profile context and inspect relevant KB state before acting.
