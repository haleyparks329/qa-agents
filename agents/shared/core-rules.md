# Core QA Agent Rules

These rules are repo-agnostic and apply to every agent in this system.

- Use the active profile for app context before making test recommendations.
- Keep output grounded in available artifacts: feature requests, profile fields, KB records, coverage reports, mutation reports, and git diff data.
- Treat generated data and examples as simulated unless a user explicitly provides public fixtures.
- Record agent outcomes as `acted`, `blocked`, or `abstained`.
- Record durable findings in the KB when a run produces gaps, observations, bug suspects, patches, or handoff debt.
- Prefer advisory routing over automatic dispatch.
- Do not include private company names, credentials, internal URLs, customer data, or production metrics.
