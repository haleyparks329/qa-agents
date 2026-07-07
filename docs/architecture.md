# Architecture

`qa-agents` is built as a small deterministic pipeline.

```text
Markdown feature request
        |
        v
qa_agents.parser
        |
        v
FeatureRequest dataclass
        |
        v
qa_agents.profiles loads JSON profile
        |
        v
qa_agents.generator combines feature + profile context
        |
        v
TestPlan dataclass
        |
        v
qa_agents.renderer emits Markdown
```

## Modules

- `qa_agents.cli`: command-line interface and error handling.
- `qa_agents.parser`: extracts a title, summary, and bullet requirements from Markdown.
- `qa_agents.profiles`: loads and validates profile JSON.
- `qa_agents.generator`: applies deterministic planning rules.
- `qa_agents.renderer`: formats the plan as Markdown.
- `qa_agents.models`: dataclasses shared across the pipeline.

## Design choices

- Keep profile context in JSON so it is easy to review and version.
- Keep generated output deterministic so tests can assert behavior.
- Keep the prototype local-first and dependency-light.
- Make the demo honest: it plans tests, but it does not execute an app or claim production coverage.

## Data boundary

The project should only use simulated or generic data. Profiles should describe app categories, not private implementations.
