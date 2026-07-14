# QA Agents Intent And Live Target Audit

## 1. Executive Verdict

`qa-agents` is not merely a set of agents that generate QA artifacts. The current repository is best understood as the foundation for an application-aware QA intelligence layer: profiles provide product context, agent specs define specialized QA roles, the SQLite KB defines durable memory, deterministic utilities detect and route narrow gap records, and the Herbie CLI demonstrates a small profile-aware planning slice.

The repo does not yet complete the intended evidence loop. It does not operate against a live application repository, execute real tests, observe product behavior, capture execution evidence, diagnose failures, or feed those results back into durable QA state. That absence is now the primary product blocker.

The right next move is not to expand all agents. The right next move is to add a small controlled target application repository and prove one complete loop:

```text
software change -> profile context -> risk-aware QA plan -> test selection/execution -> evidence capture -> KB record -> reviewable next action
```

Until that loop exists, the repo proves thoughtful architecture and disciplined boundaries, but not yet a working QA operating system.

## 2. Recovered Product Thesis

### What The Repository Currently Appears To Be

The repo currently appears to be a public-safe QA agent operating-system prototype with:

- Markdown role specifications for Herbie, Mender, Scout, Quill, and Auditor.
- Shared agent rules.
- Generic application profiles for ecommerce and SaaS dashboard contexts.
- A profile inspection CLI.
- A SQLite knowledge-base schema and helper CLI.
- Stable error fingerprinting.
- A deterministic gap detector for changed Python files, coverage JSON, and mutation JSON.
- A deterministic Herbie prototype that turns a simulated feature request into a QA plan and optional illustrative Playwright-style stubs.
- Tests covering these implemented foundations.

The executable center today is deterministic infrastructure, not autonomous agents.

### What Larger System The Architecture Suggests

The architecture points toward a persistent QA engineering layer that:

- Maintains an application model through profiles.
- Observes code, tests, failures, coverage, mutations, and human decisions.
- Routes QA work to specialized roles.
- Stores facts about plans, gaps, failures, patches, abstentions, and blocked work.
- Learns from prior QA history through KB queries and fingerprints.
- Produces reviewable next actions rather than unreviewed autonomous changes.

The durable product is not any one agent. It is the combination of application model, QA memory, deterministic execution/evidence adapters, and reviewable agent routing.

### Where Implementation Has Drifted Toward Isolated Demos

The working Herbie path starts from `examples/feature_request.md`, uses a generic profile, and generates a Markdown plan. It does not inspect a target repository or application behavior. The generated Playwright-style stubs explicitly require replacement with app-specific locators.

The gap detector can create routable records from diffs, coverage, and mutation reports, but those reports are not yet produced by an integrated application-under-test workflow.

The agent specs describe broader responsibilities than the code currently executes. That is acceptable because docs label them as prototype or planned, but it means the current product is still pre-operational.

### What Is Genuinely Distinctive

The distinctive idea is not "AI writes tests." The distinctive idea is "QA agents start from durable application context and persistent QA history." The repo is strongest where it treats QA as an ongoing system of memory, risk, evidence, routing, and review.

## 3. Current Versus Intended Workflow

### Current Workflow

```text
simulated feature request
-> selected generic profile
-> deterministic Herbie-style plan
-> optional illustrative test stubs
```

Additional disconnected utility flow:

```text
git diff / coverage JSON / mutation JSON
-> deterministic gap detection
-> SQLite gap_records
-> advisory route-gaps
```

Additional support flow:

```text
profile name
-> profile.py
-> structured agent context
```

### Intended Workflow

```text
software change
-> application context
-> risk analysis
-> QA plan
-> test selection or creation
-> execution
-> evidence capture
-> diagnosis
-> persistent state
-> review and follow-up
```

### Stage Classification

| Stage | Current status | Notes |
| --- | --- | --- |
| Software change | Implemented but weakly connected | `gap_detector.py` can inspect git diff paths. There is no observed target app change scenario. |
| Application context | Implemented and exercised | Directory profiles and `profile.py agent-context` work, but profiles are generic and point to `"repo_root": "."`. |
| Risk analysis | Implemented in prototype | Herbie uses profile risks and keyword classification for simulated feature requests. |
| QA plan | Implemented and exercised | `python -m qa_agents ...` generates a deterministic Markdown plan. |
| Test selection | Represented by prototype | Automation candidates are chosen, but not mapped to real existing tests. |
| Test creation | Stub only | Playwright-style stubs are illustrative and not repo-aware. |
| Execution | Missing | No unit/API/E2E runner integration against an application-under-test. |
| Evidence capture | Implemented but not connected | KB schema can store observations, bugs, patches, gaps, and runs; current CLIs do not capture real execution evidence. |
| Diagnosis | Represented by foundations | Fingerprinting exists; no failure ingestion or root-cause workflow exists. |
| Persistent state | Implemented and exercised narrowly | SQLite migrations, stats, queries, and gap routing work. |
| Review and follow-up | Specification/prototype | Advisory routing exists; no review queue, dashboard, PR draft, or tracker draft workflow is connected end to end. |

## 4. Missing Operating-Loop Analysis

The missing operating loop is the gap between "we can model QA work" and "we can perform QA work against a real application."

The current repo has the concepts needed to remember and route QA work, but it lacks the evidence source that would make those records meaningful. Without a target application:

- Herbie cannot tie risks to real routes, components, APIs, or tests.
- Quill cannot author or update real tests.
- Mender cannot observe failing Playwright runs or propose selector repairs.
- Scout cannot probe a running surface.
- Auditor cannot compare intended coverage to actual coverage.
- The KB cannot accumulate trustworthy history beyond synthetic records.

Yes: the absence of a live application-under-test is the primary blocker. The next blocker after that will be execution adapters: test runner invocation, artifact capture, and KB write contracts.

## 5. Target Repository Recommendation

### Option A: Continue With Simulated Requests And Profiles

Pros:

- Lowest implementation difficulty.
- Keeps docs and examples public-safe.
- Good for explaining architecture.

Cons:

- Does not prove the system can operate.
- Cannot validate agent decisions against real outcomes.
- Produces portfolio evidence that looks thoughtful but incomplete.
- Risks further drift into artifact generation rather than QA engineering.

Verdict: useful for docs and smoke tests, but not enough for the next product step.

### Option B: Create A Controlled Reference Application Repository

Pros:

- Best debugging clarity.
- High reproducibility.
- Lets you seed known failures, risky changes, coverage gaps, and flaky-like scenarios deterministically.
- Strong portfolio value because the evidence loop can be demonstrated end to end.
- Avoids coupling QA Agents to another unfinished flagship system.
- Enables stable fixtures for CI, KB snapshots, and before/after demos.

Cons:

- Requires creating and maintaining a small real app.
- Adds a second repo and integration surface.
- Must be kept deliberately small to avoid becoming the product.

Verdict: recommended first approach.

### Option C: Point Immediately At Career Intelligence

Pros:

- Highest realism.
- More meaningful domain complexity.
- Could reveal real QA needs.

Cons:

- Harder debugging because both systems may move at once.
- Lower reproducibility for public demos.
- Risk of coupling two unfinished systems.
- Public/private boundaries are more sensitive.
- Harder to seed known failures intentionally.

Verdict: valuable later, but premature for proving the first complete loop.

### Recommendation

Create a controlled reference application repository first. Use it as the QA laboratory. Once QA Agents can complete one loop there, graduate to a real existing repo as a second validation phase.

## 6. Proposed QA Laboratory

### Purpose

The target repo should be a small but real application whose main job is to exercise QA Agents. It should be boring enough to understand quickly and real enough to produce meaningful failures, coverage gaps, browser traces, API responses, and product-risk decisions.

### Product Domain

Use a compact ecommerce checkout app. Ecommerce is preferable because the current default profile already models storefront risk, and checkout has natural QA-critical flows.

### Technology Stack

- Frontend: React + Vite + TypeScript.
- Backend/API: FastAPI or Express.
- Persistence: SQLite with deterministic seed data.
- Unit/API tests: pytest for FastAPI or Vitest/Supertest for Express.
- E2E tests: Playwright.
- CI: GitHub Actions running lint, unit/API tests, Playwright tests, and coverage export.

Keep the stack conventional. The point is to test QA Agents, not to showcase a novel app architecture.

### Critical Flows

- Browse catalog.
- Filter products.
- Add item to cart.
- Edit cart quantity.
- Apply promotion code.
- Complete mock checkout.
- View order confirmation.
- Restore saved cart for a returning mock user.

### Risk Areas

- Cart totals and pricing accuracy.
- Promotion edge cases.
- Duplicate checkout submission.
- Inventory changes after cart edits.
- Saved-cart state after sign-in.
- Mobile checkout layout.
- Recoverable validation errors.

### Initial Tests

- Unit tests for pricing, promotion, cart quantity, and inventory functions.
- API tests for cart add/update, promotion application, checkout, and order retrieval.
- Playwright tests for catalog-to-checkout happy path, saved-cart reminder, promotion validation, and checkout interruption recovery.
- Coverage JSON generation.
- Optional mutation report fixture for seeded scenarios.

### Intentional Seeded Defects Or Change Scenarios

Start with scenarios that QA Agents can detect and route:

- Pricing bug: discount applies before quantity multiplication.
- Saved-cart bug: dismissed reminder returns after refresh.
- Checkout bug: double-click creates duplicate order.
- Coverage gap: changed pricing function lacks unit coverage.
- Mutation survivor: promotion validation accepts expired code.
- Selector rot: checkout button accessible name changes.
- API regression: cart quantity zero is accepted.

Each scenario should live on a named branch or fixture patch so it can be replayed.

### Artifacts QA Agents Should Consume

- App profile pointing to the target repo root.
- Git diff for a known change branch.
- Existing test inventory.
- Coverage JSON.
- Playwright JSON/JUnit report.
- Playwright trace/video/screenshot path when available.
- API test output.
- Mutation report fixture.
- Seed data description.
- Critical-flow manifest.

### Artifacts QA Agents Should Produce

- QA plan linked to changed surfaces and critical flows.
- `gap_records` for missing tests or surviving mutants.
- Execution records with command, exit code, artifact paths, and summary.
- Failure fingerprints for failing tests.
- Bug suspect records with reproduction steps and evidence paths.
- Reviewable next action: write test, inspect failure, accept risk, or patch.
- Optional test draft only after the first evidence loop is working.

### Profile Connection

Add a profile in `qa-agents` such as `profiles/reference_store/profile.json`:

- `repo_name`: the target repo name.
- `repo_root`: absolute or workspace-relative path to the target checkout.
- `test_layout.e2e`: Playwright test path.
- `test_layout.unit_or_integration`: unit/API test path.
- `tools.coverage_reports`: target coverage output path.
- `tools.playwright_reports`: target Playwright report path.
- `critical_flows`: structured flow names and routes.
- `risk_areas`: mapped to app components or API endpoints.

The profile should become the bridge between repos. QA Agents should not hardcode the target app.

## 7. First Complete Agent Loop

### Options Compared

| Loop | Strength | Weakness |
| --- | --- | --- |
| Herbie plan -> Quill test -> Playwright execution -> KB result | Shows plan-to-test value | Requires repo-aware test authoring before execution evidence is solid. |
| Failing test -> fingerprint -> Mender diagnosis -> reviewable patch | Very concrete | Patch generation and selector healing are easy to overbuild too soon. |
| Git diff -> Auditor gap -> route -> Quill test | Good use of existing gap detector | Still risks stopping at routing without real execution. |
| Profile-guided Scout mission -> browser evidence -> bug record | Strong demo | Browser exploration is open-ended and harder to make deterministic. |

### Recommended First Loop

Start with:

```text
git diff in reference app
-> profile-guided risk summary
-> run existing targeted tests
-> ingest coverage/test report
-> create KB execution + gap/failure records
-> route one reviewable next action
```

This should be an Auditor/Herbie foundation loop, not a full Quill or Mender loop yet.

Why this loop first:

- It uses the existing profile, KB, gap detector, and routing foundations.
- It includes real execution and persistent evidence.
- It avoids AI-authored tests until the system can observe reality.
- It creates the minimum substrate Mender and Quill will later need.
- It can be deterministic enough for CI and portfolio demonstration.

The first successful demo should end with a KB state that says something like:

```text
Change touched pricing logic.
Existing tests ran.
Coverage report shows changed pricing lines uncovered.
Gap record created: missing_unit_test app/pricing.py.
Recommended agent: quill.
Reviewable next action: add pricing regression for quantity + discount ordering.
```

## 8. Agent Responsibility Matrix

| Agent | Trigger | Inputs | Deterministic responsibilities | AI-assisted responsibilities | Allowed outputs | Block/abstain conditions | KB reads | KB writes | Human boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Herbie | Feature request, git change, ticket, planned release | Profile, diff summary, critical flows, past gaps | Load profile, map changed paths to risk areas, classify test types | Explain risk, draft QA plan, suggest test strategy | QA plan, risk summary, handoff recommendations | Missing profile, insufficient change context, no app mapping | gaps, prior observations, blocks, recurrences | agent_runs, observations, handoff_debt | Human accepts plan before test generation or patching |
| Auditor | Scheduled audit, diff audit, coverage/mutation report, "check gaps" | Profile, KB, test inventory, coverage, mutation data | Detect changed files, uncovered lines, surviving mutants, stale open gaps | Interpret coverage meaning, prioritize gaps | gap_records, audit summary, route recommendations | No reports available, profile paths invalid, target repo missing | gaps, tests, patches, observations, agent_runs | gap_records, observations, agent_runs | Human decides whether to accept risk or route work |
| Quill | Accepted QA plan, open gap, bug needing regression | Profile, plan, gap record, target test layout, existing tests | Locate test directories, preserve test framework conventions, run focused tests after edit | Draft or update tests, choose assertions | Test patch/draft, run result, blocked note | No runnable target repo, unclear expected behavior, unsafe fixture assumptions | gaps, bugs, prior test records | patches, tests, observations, agent_runs | Human reviews test changes before merge |
| Mender | Failing E2E/API test, CI failure, selector rot | Failure output, trace/screenshot, profile, fingerprint history | Fingerprint failure, group recurrences, identify failing command/artifacts | Diagnose likely root cause, propose selector/app/test fix | Diagnosis, patch draft, bug suspect, abstention | Failure is product bug not test rot, missing trace, nondeterministic failure | bugs, recurrences, pending patches | bugs, patches, observations, agent_runs | Human approves patch, especially when app behavior changes |
| Scout | Smoke/probe request, new feature surface, exploratory mission | Profile, running app URL, seed data, critical flows | Use bounded mission, capture reproduction steps and artifacts | Explore edge cases, identify suspicious behavior | bug suspect, evidence note, abstention | App unavailable, auth/seed data missing, mission too broad | bugs, prior observations, gaps | bugs, observations, agent_runs | Human confirms whether suspect is a bug |

### Overlaps To Watch

- Herbie and Auditor can both produce coverage recommendations. Herbie should plan from intent and risk; Auditor should evaluate evidence and drift.
- Quill and Mender can both edit tests. Quill should create coverage/regression tests; Mender should repair failing tests or diagnose whether the app changed.
- Scout and Auditor can both find gaps. Scout finds behavior through exploration; Auditor finds gaps through artifacts and history.
- Mender must not silently turn product failures into test fixes. It should record an abstention or bug suspect when behavior appears genuinely broken.

## 9. Revised Architecture

Center the product on application-aware QA intelligence:

```text
target application repo
        |
        v
repository/change observer
        |
        v
application profile/model
        |
        v
execution adapters ----------------+
        |                           |
        v                           |
artifact store                      |
        |                           |
        v                           |
QA knowledge base <----------------+
        |
        v
agent workers
        |
        v
routing/review layer
```

### Components

- Application profile/model: structured context for critical flows, risks, test layout, tools, seed data, constraints, and known boundaries.
- Repository/change observer: reads git diffs, changed paths, dependency changes, test inventory, and scenario branches.
- Execution adapters: run unit/API/E2E/coverage/mutation commands and normalize outputs.
- Artifact store: stores or references reports, screenshots, traces, logs, coverage files, and generated plans.
- QA knowledge base: records runs, observations, gaps, failures, fingerprints, patches, tests, handoffs, blocks, and abstentions.
- Agent workers: Herbie, Auditor, Quill, Mender, Scout as bounded role-specific processors.
- Routing/review layer: turns state into reviewable next actions without automatic dispatch by default.

### Deterministic Versus LLM Responsibilities

Keep deterministic:

- Profile loading and validation.
- Git diff parsing.
- Test command execution.
- Coverage and mutation ingestion.
- Fingerprinting.
- KB writes and schema migrations.
- Gap type routing defaults.
- Artifact path capture.
- Exit status handling.

Use LLMs where they add value:

- Explaining product risk from profile + diff context.
- Prioritizing among competing gaps.
- Drafting human-readable plans and bug summaries.
- Proposing test cases once expected behavior is known.
- Diagnosing whether a failure looks like selector rot, test drift, or product bug.
- Writing reviewable patch drafts after deterministic evidence exists.

## 10. Engineering Evidence Assessment

### Strongest Current Evidence

- Clear product architecture with honest status boundaries.
- Public-safe framing and generic profiles.
- Good separation between profiles, shared rules, agent specs, KB, and prototype CLI.
- SQLite schema that anticipates durable QA memory.
- Deterministic gap detection and routing rather than vague agent magic.
- Tests covering the implemented surfaces.
- Recent commit history shows correction from a simplified planner demo toward the original broader architecture.

### Weak Or Missing Evidence

- No target application-under-test.
- No real test execution adapter.
- No Playwright report, trace, screenshot, or coverage ingestion loop from a target app.
- No persisted agent run lifecycle around a real QA task.
- No repo-aware test authoring.
- No Mender diagnosis or patch workflow.
- No Scout browser probing.
- No dashboard or review queue.
- No proof that historical KB state improves later decisions.

### What A Live Target Repository Would Prove

- The system can observe real code changes.
- Profiles can map to actual routes, tests, and risk surfaces.
- QA plans can drive real execution decisions.
- Gap records can be derived from real reports.
- Failure fingerprints can identify recurrences.
- The KB can become useful memory rather than an empty schema.
- The architecture can produce reviewable next actions from evidence.

### What Not To Build Merely For Portfolio Appearance

- A polished dashboard before evidence exists.
- Full autonomous orchestration.
- Five expanded agents at once.
- LLM-heavy test generation without execution.
- Slack/digest workflows before the KB has meaningful state.
- A complex target app that becomes a second flagship.
- Auto-PR creation before patch quality and review boundaries are proven.

### Should This Remain A Flagship Project?

Yes, if it becomes evidence-driven. The concept is strong and differentiated. But its flagship value depends on proving the operating loop against a real app. As-is, it is a promising architecture prototype; with a controlled target repo and one complete loop, it can become a credible demonstration of QA systems engineering.

## 11. Small Phased Plan

### Phase 1: Create The QA Laboratory

- Create a separate small reference ecommerce app repo.
- Add deterministic seed data.
- Add unit/API tests and Playwright tests.
- Add coverage output.
- Add CI.
- Add named scenario branches or patch fixtures with seeded defects.

### Phase 2: Connect Profile To Target Repo

- Add `profiles/reference_store/`.
- Point profile fields to the target repo paths and report artifacts.
- Add profile validation for required target-repo fields.
- Keep existing generic profiles intact.

### Phase 3: Build Execution Evidence Adapter

- Add a narrow command that runs configured tests for the active profile.
- Capture command, exit code, stdout/stderr summary, and artifact paths.
- Record an `agent_run` and `observation` in the KB.
- Do not generate tests yet.

### Phase 4: Complete First Loop

- Given a target app diff, run profile-guided test/coverage checks.
- Ingest coverage JSON.
- Create structured `gap_records`.
- Route gaps.
- Produce one reviewable next action.

### Phase 5: Add One Agent Capability

- Add Quill only for one gap type: `missing_unit_test`.
- Require a human-accepted expected behavior.
- Write one focused regression test.
- Run it.
- Record patch and evidence in KB.

### Phase 6: Add Failure Diagnosis

- Add Mender for one failure type: selector/name drift in Playwright.
- Fingerprint failures.
- Distinguish test rot from product bug.
- Produce reviewable patch or abstention.

## 12. Things Not To Build Yet

- Do not expand all five agents simultaneously.
- Do not build the dashboard before the KB contains real records.
- Do not add Slack/digest automation yet.
- Do not point first at Career Intelligence.
- Do not make the reference app large or clever.
- Do not auto-dispatch agents from `route-gaps`.
- Do not auto-open PRs until test execution and patch review are stable.
- Do not use LLM output as evidence; evidence should come from repo state, test runs, reports, and captured artifacts.

## 13. Open Product Decisions Requiring Haley's Judgment

- Should the reference app live under the same GitHub account as a public demo, or remain private until the loop is polished?
- Should the first target app be ecommerce, matching the existing profile, or SaaS dashboard, matching a more portfolio-relevant business context?
- Should QA Agents own execution, or should it observe CI artifacts produced elsewhere?
- What level of autonomy is acceptable for test patches: draft only, branch only, or PR draft?
- What should count as durable QA memory versus ephemeral run logs?
- How much LLM usage should be visible in the public demo?
- Should the KB remain local-first SQLite only, or eventually support exportable review artifacts for portfolio demos?
- Which evidence artifact matters most for the first public story: coverage gap, failing E2E trace, bug suspect, or accepted regression test?
