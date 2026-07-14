# Demo

All demo data is simulated and public-safe.

## Implemented: Beacon Prototype

The runnable planner is a small Beacon slice. It exists to show profile-aware
QA scoping without claiming full agent orchestration.

```bash
python -m qa_agents examples/feature_request.md --profile ecommerce
```

With generic Playwright-style stubs:

```bash
python -m qa_agents examples/feature_request.md --profile ecommerce --stubs
```

Save the plan:

```bash
python -m qa_agents examples/feature_request.md --profile ecommerce --stubs --output qa_plan_output.md
```

## Implemented: Profile Context

```bash
python3 profile.py --profile ecommerce agent-context beacon
python3 profile.py --profile ecommerce agent-context gap-detector
```

## Implemented: KB And Gap Records

```bash
export QA_KB_PATH=/tmp/qa-agents-demo.db
python3 kb.py migrate
python3 kb.py stats
python3 gap_detector.py --base origin/main --head HEAD --route
python3 kb.py query gaps
python3 kb.py route-gaps
```

## Prototype Output Shape

The Beacon prototype output includes:

- selected profile
- parsed feature summary and requirements
- deterministic test cases
- test type classifications
- risk notes
- automation candidates
- optional generic Playwright-style stubs

## Planned Demos

- Live dashboard or tracker.
- Digest workflow.
- Playwright healing.
- Browser probing.
- Automated multi-agent handoffs.
