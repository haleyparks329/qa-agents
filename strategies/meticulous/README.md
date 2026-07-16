# Meticulous-Inspired Replay Strategy

This is an independent technical exploration based on publicly documented replay-testing concepts. It is not an official Meticulous integration and does not use private Meticulous APIs or data.

All replay evidence in this directory is synthetic and explicitly marked as
simulated.

## Problem

Replay systems can produce large amounts of high-quality deterministic
evidence, but engineers must still turn that evidence into an engineering
decision.

## Hypothesis

Specialized QA agents can operate downstream of deterministic replay
infrastructure to:

- group affected sessions into workflows;
- separate expected changes from regressions;
- identify shared causes;
- detect missing workflow coverage;
- recommend a bounded next action.

## Architectural boundary

```text
Replay platform responsibilities:
- session capture
- replay
- network virtualization
- base/head comparison
- raw evidence generation

QA Agents responsibilities:
- normalization
- clustering
- investigation
- coverage interpretation
- risk synthesis
- recommendation
```

## Key principle

> Deterministic systems produce the evidence. Probabilistic systems interpret the evidence. Humans retain authority.

## Demo flow

```text
Deterministic replay evidence
        ↓
Evidence normalization
        ↓
Workflow clustering
        ↓
Investigation
        ↓
Risk and confidence assessment
        ↓
Human decision
```

Run the fixture:

```bash
python3 -m qa_agents investigate \
  --strategy meticulous \
  --input strategies/meticulous/fixtures/pricing-change.input.json
```

Expected result:

```text
17 affected replay sessions
3 affected user workflows
1 confirmed regression
1 expected product change group
1 uncovered changed branch
Recommended merge decision: hold
```
