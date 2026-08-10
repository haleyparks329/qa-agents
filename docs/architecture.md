# Public Architecture

QA Agents separates four concerns that are often blurred together:

1. **Evidence:** deterministic observations such as a diff, test result, or coverage artifact.
2. **Investigation:** a bounded role interprets what the evidence can and cannot support.
3. **Proposed work:** a test, repair, or follow-up may be suggested.
4. **Authority:** a human decides what to accept, run, change, or merge.

`acted`, `blocked`, and `abstained` describe the investigation outcome. They prevent missing evidence or missing authority from being smoothed into false completion.

This public architecture intentionally excludes persistence, schemas, profiles, prompts, policies, routing, fingerprinting, tool permissions, and runtime composition.
