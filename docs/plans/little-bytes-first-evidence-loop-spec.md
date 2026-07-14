# Little Bytes First Evidence Loop Specification

## 1. Scope

This specification defines the smallest complete evidence loop between `qa-agents` and a future controlled reference application named **Little Bytes**.

Little Bytes is a small online bakery where customers can browse baked goods, customize orders, apply coupons, and place pickup or delivery orders. Its purpose is to exercise QA Agents under controlled, reproducible conditions. It is not intended to become another flagship product.

The first loop is:

```text
target repository git diff
-> application profile
-> deterministic test execution
-> coverage/test artifact ingestion
-> persistent execution and gap records
-> advisory reviewable next action
```

The first implementation should prove that QA Agents can observe a real target repo, run configured checks, normalize evidence, persist records, and recommend one reviewable next action. It should not generate tests, open patches, or expand agent autonomy.

## 2. Non-Goals

- Do not create the Little Bytes repository in this phase.
- Do not implement the execution adapter in this phase.
- Do not add AI-authored tests.
- Do not expand Quill, Mender, Scout, or dashboard surfaces.
- Do not build an AI bakery.
- Do not build an autonomous agent dispatcher.
- Do not auto-open pull requests or tracker tickets.
- Do not require hardcoded absolute paths.
- Do not use an LLM to interpret raw test output in the first implementation.
- Do not make Little Bytes large, clever, or production-like.

## 3. Little Bytes Application Contract

### Product Shape

Little Bytes should be a deliberately small but real application:

- React + Vite + TypeScript frontend.
- Small FastAPI backend unless another simple backend becomes clearly easier.
- SQLite persistence.
- Deterministic seed data.
- Unit tests.
- API tests.
- Playwright end-to-end tests.
- Coverage JSON output.
- GitHub Actions workflow.

The app should favor deterministic behavior, simple code paths, and repeatable failure scenarios.

### Initial User Flows

Include only the behavior needed to exercise QA workflows:

- Browse bakery catalog.
- View product detail.
- Add item to cart.
- Update quantity.
- Add optional custom message.
- Apply coupon.
- Select pickup or delivery.
- Complete checkout.
- View order confirmation.

### Catalog Fixtures

Seed deterministic products with fixed prices and inventory:

| Product | Example price | Example inventory |
| --- | ---: | ---: |
| Chocolate Chip Cookies | 3.50 | 24 |
| Croissants | 4.25 | 18 |
| Cinnamon Rolls | 4.75 | 12 |
| Cupcakes | 3.25 | 30 |
| Lemon Bars | 3.75 | 16 |
| Cheesecake | 6.50 | 8 |
| Sourdough Bread | 7.00 | 10 |
| Matcha Latte | 5.25 | 20 |

Exact values can change during implementation, but they must remain deterministic and committed with the seed data.

### Critical Risk Areas

The application profile should model these as first-class QA risks:

- Pricing accuracy.
- Coupon calculations.
- Inventory availability.
- Pickup scheduling.
- Checkout completion.
- Cart persistence.
- Order confirmation.
- Accessibility.
- Responsive checkout.

## 4. Cross-Repository Profile Schema

Add a future profile at:

```text
profiles/little_bytes/
  profile.json
  house-rules.md
```

The profile must be configurable across machines. Prefer workspace-relative paths, environment variable interpolation, or explicit CLI overrides. Do not require hardcoded absolute paths.

### Required Fields

The profile should extend the current profile shape with these fields:

```json
{
  "name": "little_bytes",
  "repo_name": "little-bytes",
  "repo_root": "${QA_TARGET_REPO_ROOT:-../little-bytes}",
  "app_description": "A small deterministic online bakery used as a QA Agents reference application.",
  "source_paths": {
    "frontend": "frontend/src",
    "backend": "backend",
    "pricing": "backend/app/pricing.py",
    "coupons": "backend/app/coupons.py",
    "inventory": "backend/app/inventory.py",
    "checkout": "backend/app/checkout.py"
  },
  "test_layout": {
    "unit": "backend/tests/unit",
    "api": "backend/tests/api",
    "e2e": "frontend/tests/e2e",
    "fixtures": "seed"
  },
  "commands": {
    "unit": "python -m pytest backend/tests/unit --cov=backend/app --cov-report=json:artifacts/coverage/unit-coverage.json",
    "api": "python -m pytest backend/tests/api",
    "e2e": "npm run test:e2e -- --reporter=json"
  },
  "reports": {
    "coverage": "artifacts/coverage/unit-coverage.json",
    "api": "artifacts/test-results/api-results.json",
    "e2e": "artifacts/playwright/results.json"
  },
  "artifacts": {
    "root": "artifacts",
    "playwright_traces": "artifacts/playwright/traces",
    "screenshots": "artifacts/playwright/screenshots"
  },
  "seed_data": {
    "database": "seed/little_bytes.sqlite",
    "reset_command": "python scripts/reset_seed_data.py",
    "fixtures": ["seed/products.json", "seed/coupons.json"]
  },
  "critical_flows": {
    "catalog_browse": ["frontend/src/routes/catalog", "backend/app/catalog.py"],
    "cart_update": ["frontend/src/routes/cart", "backend/app/cart.py"],
    "coupon_apply": ["backend/app/coupons.py", "backend/app/pricing.py"],
    "checkout_complete": ["frontend/src/routes/checkout", "backend/app/checkout.py"]
  },
  "risk_area_mappings": {
    "pricing accuracy": ["backend/app/pricing.py"],
    "coupon calculations": ["backend/app/coupons.py", "backend/app/pricing.py"],
    "inventory availability": ["backend/app/inventory.py"],
    "checkout completion": ["backend/app/checkout.py"],
    "responsive checkout": ["frontend/src/routes/checkout"]
  },
  "validation": {
    "required_paths": ["backend/app", "backend/tests", "frontend/src", "frontend/tests/e2e"],
    "required_reports_after_run": ["artifacts/coverage/unit-coverage.json"]
  }
}
```

### Validation Requirements

Profile validation for this loop should verify:

- Target repo path resolves.
- Required source and test paths exist.
- Configured commands are present.
- Required report paths are relative to the target repo.
- Artifact paths are relative to the target repo.
- Critical flow mappings reference known source paths.
- Risk-area mappings reference known source paths.

Path resolution failures should block the run before any command executes.

## 5. Execution Adapter

Add a future deterministic execution component behind a unified CLI:

```bash
python -m qa_agents run \
  --profile little_bytes \
  --base main \
  --head HEAD
```

The adapter must:

- Load the active profile.
- Resolve the target repository root.
- Verify the target repository exists.
- Verify required paths exist.
- Compute changed files from `--base` and `--head` in the target repo.
- Run configured commands in the target repo.
- Capture start and end time.
- Capture duration.
- Capture exit code for each command.
- Capture bounded stdout and stderr summaries.
- Record configured artifact paths.
- Record configured report paths.
- Handle timeout.
- Handle missing commands.
- Handle missing reports.
- Write normalized execution records.
- Never interpret raw execution output with an LLM.

### Command Selection

The first implementation can run a fixed subset:

```text
unit -> coverage ingestion -> gap detection
```

API and Playwright commands should be represented in the profile but may be inactive for the first loop unless the implementation needs them for acceptance testing.

### Output

The CLI should print a concise deterministic summary:

```text
profile: little_bytes
target_repo: ../little-bytes
base: main
head: HEAD
changed_files: 1
commands:
- unit: passed, exit_code=0, duration_ms=...
reports:
- coverage: artifacts/coverage/unit-coverage.json, found
gaps:
- missing_unit_test backend/app/pricing.py
recommended_next_action:
Quill should create a regression test for quantity and discount ordering.
```

## 6. Evidence Normalization

### Execution Result

Normalize each command run into a structured record:

```json
{
  "command_name": "unit",
  "command": "python -m pytest ...",
  "cwd": "../little-bytes",
  "status": "passed",
  "exit_code": 0,
  "started_at": "ISO-8601",
  "finished_at": "ISO-8601",
  "duration_ms": 1234,
  "stdout_summary": "bounded text",
  "stderr_summary": "bounded text",
  "timeout_seconds": 120,
  "artifact_refs": ["artifacts/coverage/unit-coverage.json"]
}
```

Allowed statuses:

- `passed`
- `failed`
- `timed_out`
- `missing_command`
- `missing_report`
- `blocked`

### Changed Files

Normalize changed files from the target repo as paths relative to the target repo root:

```json
{
  "base": "main",
  "head": "HEAD",
  "files": ["backend/app/pricing.py"]
}
```

### Coverage Evidence

Coverage ingestion should extract only the facts needed for the first loop:

```json
{
  "report_path": "artifacts/coverage/unit-coverage.json",
  "files": {
    "backend/app/pricing.py": {
      "missing_lines": [42, 43],
      "covered_lines": [10, 11, 12]
    }
  }
}
```

### Changed Uncovered Lines

The first loop should derive:

```json
{
  "path": "backend/app/pricing.py",
  "gap_type": "missing_unit_test",
  "detail": "changed pricing file has uncovered changed lines"
}
```

If line-level diff parsing is too much for the first implementation, the fallback may be file-level:

```text
changed Python file has uncovered lines
```

The line-level version is preferred, but file-level detection is acceptable for the first working pass.

### Failure Fingerprints

Failure fingerprinting should reuse `fingerprint_error()` when a command fails and bounded stderr/stdout contains a stable failure string. The first pricing coverage loop does not require failure diagnosis.

### Gap Records

Gap records should reuse the existing `gap_records` table where practical:

- `gap_type`: `missing_unit_test`
- `path`: target-repo-relative path, such as `backend/app/pricing.py`
- `detail`: short deterministic explanation
- `recommended_agent`: `quill` after routing
- `route_reason`: `test authoring gap`

### Artifact References

Artifact references should be paths relative to the target repo root:

```json
{
  "kind": "coverage_report",
  "path": "artifacts/coverage/unit-coverage.json",
  "exists": true
}
```

Do not copy large raw artifacts into the KB. Store references and bounded summaries.

## 7. KB Mapping

Reuse the existing SQLite schema as much as possible.

### Existing Tables To Use

- `agent_runs`: one run for the deterministic evidence loop.
- `observations`: bounded summaries, block reasons, missing report notices, and reviewable next action.
- `gap_records`: uncovered changed code and routed next actions.
- `bugs`: only when a test failure is normalized into a bug suspect in later phases.
- `patches`: not used in the first loop.
- `tests`: not required in the first loop unless recording discovered test paths is trivial.

### Minimal New Migration

The first execution loop likely needs one small table for normalized command evidence:

```sql
CREATE TABLE IF NOT EXISTS execution_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER,
  command_name TEXT NOT NULL,
  command TEXT NOT NULL,
  cwd TEXT NOT NULL,
  status TEXT NOT NULL,
  exit_code INTEGER,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  duration_ms INTEGER,
  stdout_summary TEXT,
  stderr_summary TEXT,
  artifact_refs_json TEXT NOT NULL DEFAULT '[]',
  report_refs_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (run_id) REFERENCES agent_runs(id)
);
```

Avoid adding many tables until there is repeated evidence that they are needed.

### Durable Memory Versus Ephemeral Logs

Durable QA memory:

- Run status.
- Command status and exit code.
- Artifact/report references.
- Coverage-derived gaps.
- Failure fingerprints.
- Reviewable next action.
- Blocked or abstained outcome.

Ephemeral logs:

- Full stdout.
- Full stderr.
- Full Playwright trace bodies.
- Full coverage files.
- Raw screenshots/videos.

External artifacts:

- Coverage JSON.
- Playwright JSON report.
- Playwright traces.
- Screenshots.
- CI logs.

The KB should store references to external artifacts, not large raw payloads.

## 8. Replayable Bakery Scenarios

Little Bytes should contain deterministic scenario branches or patch fixtures:

| Scenario | Purpose | Expected QA Agents signal |
| --- | --- | --- |
| Pricing: quantity/discount ordering bug | Pricing logic changed incorrectly | Changed pricing file plus uncovered lines creates `missing_unit_test`. |
| Inventory: sold-out item still purchasable | Inventory risk and API validation | API/E2E failure or bug suspect in later phase. |
| Coupons: discount stacking incorrectly | Coupon calculation risk | Unit/API failure or missing regression gap. |
| Checkout: double-click creates duplicate order | Checkout completion and idempotency risk | E2E failure or bug suspect in later phase. |
| Coverage: changed pricing function lacks regression coverage | First evidence-loop scenario | `missing_unit_test` routed to Quill. |
| Mutation: expired coupon mutation survives | Mutation ingestion in later phase | `surviving_mutant` routed to Quill. |
| Playwright: accessible name changes break selectors | Selector/test drift in later phase | `playwright_failure` routed to Mender. |

All scenarios must be replayable locally and in CI.

## 9. CLI Contract

### Primary Command

```bash
python -m qa_agents run \
  --profile little_bytes \
  --base main \
  --head HEAD
```

### Options

- `--profile`: required for the first implementation.
- `--base`: git base ref in the target repo; default may be `main`.
- `--head`: git head ref in the target repo; default may be `HEAD`.
- `--command`: optional repeatable command selector, such as `unit`, `api`, or `e2e`.
- `--timeout`: per-command timeout in seconds.
- `--json`: emit normalized machine-readable summary.
- `--dry-run`: validate profile, resolve paths, and print planned commands without executing them.

### Exit Codes

- `0`: deterministic run completed and records were written, even if gaps were found.
- `1`: run completed but one or more configured commands failed.
- `2`: blocked before execution due to profile/path/configuration error.
- `3`: timed out.
- `4`: KB write failed.

Finding a QA gap should not itself be a process failure.

## 10. Error Handling

### Missing Target Repo

Status: `blocked`

Record:

- Observation kind: `blocked`
- Message: target repository path could not be resolved or does not exist.

### Invalid Profile

Status: `blocked`

Block before command execution. Include the missing field or invalid path.

### Missing Command

Status: `missing_command`

Record an execution record. Do not guess an alternate command.

### Timeout

Status: `timed_out`

Record bounded output collected before termination. Mark the run as `blocked` unless other required commands completed and evidence is still usable.

### Missing Report

Status: `missing_report`

Record the command result and missing report path. If coverage is required for the first loop, block gap detection and write a reviewable action to fix report generation.

### Command Failure

Status: `failed`

Record exit code and bounded output. Use fingerprinting only for stable failure text. Do not ask an LLM to diagnose the failure in the first implementation.

### No Relevant Changed Files

Status: `abstained`

Record that the run found no target-relevant changed files for the selected profile and therefore did not create a gap.

## 11. Local And CI Execution

### Local

Expected local flow after Little Bytes exists:

```bash
export QA_TARGET_REPO_ROOT=../little-bytes
export QA_KB_PATH=/tmp/qa-agents-little-bytes.db
python -m qa_agents run --profile little_bytes --base main --head HEAD
python kb.py query gaps
python kb.py route-gaps
```

The CLI may route gaps automatically only as part of the deterministic run summary. It must not dispatch an agent.

### CI

CI should be able to run the same scenario from a clean checkout:

- Checkout `qa-agents`.
- Checkout or create the Little Bytes target repo at a known relative path.
- Install dependencies.
- Reset deterministic seed data.
- Apply or checkout the pricing scenario.
- Run `python -m qa_agents run --profile little_bytes --base main --head HEAD --json`.
- Upload normalized summary and target app artifacts.

CI should not require private credentials.

## 12. Acceptance Criteria

The first implementation is acceptable when:

- `profiles/little_bytes/profile.json` validates without hardcoded absolute paths.
- The run CLI verifies the target repo exists before executing commands.
- The run CLI computes changed files from the target repo.
- The run CLI executes the configured unit/coverage command.
- The run CLI records start time, end time, duration, exit code, bounded output summaries, and artifact/report references.
- Coverage JSON is ingested deterministically.
- The pricing scenario creates one `missing_unit_test` gap for the changed pricing file.
- `route-gaps` recommends `quill` with route reason `test authoring gap`.
- The CLI prints or emits JSON with the reviewable next action: Quill should create a pricing regression test.
- Missing repo, invalid profile, missing command, timeout, missing report, command failure, and no relevant changes are covered by tests.
- No tests are generated.
- No patches are written.
- No dashboard, Scout, Mender, or expanded Quill behavior is added.

## 13. Recommended Implementation Order

1. Add profile schema extensions and validation for command/report/artifact paths.
2. Add the minimal `execution_records` migration.
3. Add KB helpers for creating and querying execution records.
4. Add a `qa_agents.run` module with dry-run profile validation.
5. Add target-repo git diff resolution.
6. Add deterministic command execution with timeout and bounded output.
7. Add coverage report ingestion.
8. Connect changed Python files plus coverage evidence to existing `record_gap()`.
9. Route gaps and emit a reviewable next action.
10. Add tests using temporary fake target repos and fixture coverage JSON.
11. Only after the above passes, create the Little Bytes repository in a separate task.

## 14. Expected Future Files

Likely future files in `qa-agents`:

```text
profiles/little_bytes/profile.json
profiles/little_bytes/house-rules.md
schema/005_execution_records.sql
qa_agents/run.py
qa_agents/execution.py
qa_agents/evidence.py
qa_agents/profile_validation.py
tests/test_run_cli.py
tests/test_execution_records.py
tests/test_little_bytes_profile.py
tests/fixtures/coverage/little_bytes_pricing_coverage.json
```

Likely future files in Little Bytes:

```text
backend/app/pricing.py
backend/app/coupons.py
backend/app/inventory.py
backend/app/checkout.py
backend/tests/unit/test_pricing.py
backend/tests/api/test_checkout.py
frontend/src/
frontend/tests/e2e/checkout.spec.ts
seed/products.json
seed/coupons.json
scripts/reset_seed_data.py
artifacts/
.github/workflows/ci.yml
```

These paths are expected, not required. The implementation may adjust them if the profile contract remains stable.

## 15. Review Boundaries

### Deterministic Responsibilities

- Load and validate profile.
- Resolve target repository path.
- Compute target-repo git diff.
- Run configured commands.
- Capture command timing and exit status.
- Bound stdout/stderr summaries.
- Validate report existence.
- Parse coverage JSON.
- Create execution records.
- Create gap records.
- Route gaps to recommended agents.
- Emit deterministic summary.

### Optional LLM Responsibilities

The first implementation should not require an LLM.

A later narrow use case may allow an LLM to turn normalized evidence into a human-readable QA summary, but only after deterministic records exist. The LLM must not be the source of factual evidence.

### Factual Outputs

- Changed files.
- Command statuses.
- Exit codes.
- Timings.
- Report paths.
- Artifact paths.
- Coverage facts.
- Gap records.
- Route recommendations.

### Recommendation Outputs

- Recommended next action.
- Recommended agent.
- Route reason.
- Optional human-readable summary based only on normalized facts.

### Block Conditions

- Missing target repo.
- Invalid profile.
- Missing required source/test paths.
- Missing required command.
- Missing required coverage report.
- Timeout with unusable evidence.
- KB write failure.

### Abstain Conditions

- No relevant changed files.
- Changed files do not map to known profile risks.
- Coverage exists but no uncovered changed files are found.
- Scenario is outside the first-loop scope, such as browser selector repair or exploratory probing.

### Required Human Approvals

- Creating the Little Bytes repository.
- Adding or changing generated tests.
- Applying patches.
- Opening PRs or tracker tickets.
- Expanding Quill, Mender, Scout, or dashboard behavior.
- Treating a failing test as a product bug versus a test maintenance issue.

## 16. Risks And Unresolved Decisions

- Path interpolation syntax must stay simple enough to validate without surprising shell behavior.
- FastAPI is preferred, but the final backend choice should optimize for reproducibility.
- Line-level changed uncovered detection is better than file-level detection, but file-level may be acceptable for the first pass.
- The target repo may need both local artifact paths and CI artifact upload conventions.
- The first execution adapter should avoid becoming a generic CI system.
- The KB may eventually need richer artifact and run tables, but the first migration should stay minimal.
- The public demo should be explicit that Little Bytes exists to test QA Agents, not to showcase bakery product work.
- The first loop should define whether a command failure exits with process code `1` even when evidence was persisted successfully.
