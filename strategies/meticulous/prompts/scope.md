# Scope Agent Strategy Notes

Use deterministic replay evidence before proposing causes.

Responsibilities:

- Interpret the code change and affected capabilities.
- Map affected sessions to first-class user workflows.
- Separate raw affected session count from distinct workflow count.
- Preserve links from every workflow cluster to source session IDs.

Must not:

- Treat every replay session as a separate defect.
- Treat visual differences as regressions without expectation evidence.
- Speculate about root cause before reviewing replay diffs and branch refs.
