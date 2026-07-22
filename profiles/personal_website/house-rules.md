# Personal Website Profile Rules

Treat the website as Haley's public system interface, not only as an Astro build. Evidence collection must be deterministic, read-only with respect to website source, and explicit about untested behavior.

The validation command covers formatting, Astro checks, production output, and internal links. It does not prove browser interaction, accessibility, screenshot, or responsive-layout behavior. Keep those limitations as structured evidence gaps, and never expose local paths, environment variables, raw logs, or secrets in a public artifact.
