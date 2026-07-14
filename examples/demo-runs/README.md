# Demo Run Artifacts

This directory contains public-safe JSON artifacts generated from real QA
Agents runs.

The Little Bytes pricing artifact comes from a real run against the public
`haleyparks329/little-bytes` reference application. It is intended for README
examples, portfolio-site replay, screenshots, and future regression checks.

The artifact does not mean Scribe executed. In this phase, QA Agents runs the
configured unit command, records coverage evidence, persists a
`missing_unit_test` gap, and recommends Scribe as the reviewable next action.
No tests or patches are generated automatically.

Regenerate the stable artifact from the `qa-agents` repository with:

```bash
export QA_TARGET_REPO_ROOT=../little-bytes
export QA_KB_PATH=/tmp/qa-agents-little-bytes-demo.db
rm -f "$QA_KB_PATH"

python -m qa_agents export-demo \
  --profile little_bytes \
  --base main \
  --head scenario/pricing-discount-order \
  --output examples/demo-runs/little-bytes-pricing.json \
  --stable
```
