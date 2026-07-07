# Demo

All demo data is simulated.

## Implemented Planner Demo

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

## Implemented Profile Demo

```bash
python3 profile.py --profile ecommerce agent-context herbie
```

## Implemented KB Demo

```bash
export QA_KB_PATH=/tmp/qa-agents-demo.db
python3 kb.py migrate
python3 kb.py stats
python3 gap_detector.py --base origin/main --head HEAD --route
python3 kb.py query gaps
```

## Prototype Output Shape

The planner output includes:

- selected profile
- parsed feature summary and requirements
- deterministic test cases
- test type classifications
- risk notes
- automation candidates
- optional generic Playwright-style stubs

## Planned Demos

- Live dashboard.
- Slack digest.
- Playwright healing.
- Browser probing.
- Automated multi-agent orchestration.
