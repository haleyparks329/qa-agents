# Demo

This demo uses simulated data only.

## Generate a plan

```bash
python -m qa_agents examples/feature_request.md --profile ecommerce
```

## Generate a plan with Playwright-style stubs

```bash
python -m qa_agents examples/feature_request.md --profile ecommerce --stubs
```

## Save the plan

```bash
python -m qa_agents examples/feature_request.md --profile ecommerce --stubs --output qa_plan_output.md
```

## Expected output shape

The generated plan includes:

- selected profile
- parsed feature summary and requirements
- three deterministic test cases
- test type classifications
- risk notes
- automation candidates
- optional Playwright-style stubs

## What to look for

The ecommerce profile should steer the plan toward cart, checkout, totals, and validation concerns. The dashboard profile should steer the same feature request toward visibility, filtering, export, and dashboard state concerns.
