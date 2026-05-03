---
name: ring:dev-implementation
description: |
  Gate 0 of the development cycle. Executes code implementation using the appropriate
  specialized agent based on task content and project language. Handles TDD workflow
  with RED-GREEN phases. Follows project standards defined in docs/PROJECT_RULES.md.
  Includes delivery verification exit criteria integrated into Gate 0.

trigger: |
  - Gate 0 of development cycle
  - Tasks loaded at initialization
  - Ready to write code
skip_when: |
  - Not inside a development cycle (ring:dev-cycle or ring:dev-refactor)
  - Task is documentation-only, configuration-only, or non-code
  - Implementation already completed for the current gate

sequence:
  before: [ring:dev-devops]

related:
  complementary: [ring:dev-cycle, ring:test-driven-development, ring:codereview]
---

# Code Implementation (Gate 0)

You orchestrate. Agents implement. Select the agent, prepare the prompt, track state, validate outputs.

## Step 1: Validate Input

Required: `unit_id`, `requirements`, `language` (go|typescript|python), `service_type` (api|worker|batch|cli|frontend|bff).
Optional: `technical_design`, `existing_patterns`, `project_rules_path` (default: `docs/PROJECT_RULES.md`).

STOP if any required input is missing.

## Step 2: Validate Prerequisites

Check `PROJECT_RULES.md` exists at `project_rules_path` → STOP if not found.

**Agent selection:**

| Language | Service Type | Agent |
|----------|--------------|-------|
| go | api, worker, batch, cli | ring:backend-engineer-golang |
| typescript | api, worker | ring:backend-engineer-typescript |
| typescript | frontend, bff | ring:frontend-bff-engineer-typescript |

## Step 3: Gate 0.1 — TDD-RED (Write Failing Test)

Dispatch selected agent:

```yaml
Task:
  subagent_type: "{selected_agent}"
  description: "TDD-RED: Write failing test for {unit_id}"
  prompt: |
    ## TDD-RED PHASE: Write a FAILING Test

    unit_id: {unit_id}
    requirements: {requirements}
    language: {language}
    service_type: {service_type}

    Standards: Load via state.cached_standards or WebFetch Ring standards for language.
    Project rules: {project_rules_path}

    ## Frontend TDD Policy (React/Next.js only)
    Visual-only components (layout, styling, animations): TDD-RED not required.
    Report "Visual-only component → TDD-RED skipped, Gate 4 snapshots apply."
    Behavioral components (hooks, validation, state, conditional rendering, API): MUST use TDD-RED.

    ## Your Task
    1. Write a test that captures expected behavior
    2. Test MUST FAIL (no implementation yet)
    3. Run test and capture FAILURE output

    ## Required Output
    - Test file path + code
    - Test command
    - Failure output (MANDATORY — include actual failure text)
```

Validate output: failure_output must contain "FAIL". Re-dispatch if missing.

## Step 4: Gate 0.2 — TDD-GREEN (Implementation)

Prerequisite: TDD-RED status = completed.

Dispatch selected agent:

```yaml
Task:
  subagent_type: "{selected_agent}"
  description: "TDD-GREEN: Implement code to pass test for {unit_id}"
  prompt: |
    ## TDD-GREEN PHASE: Make the Test PASS

    unit_id: {unit_id}
    requirements: {requirements}
    TDD-RED test file: {tdd_red.test_file}
    TDD-RED failure output: {tdd_red.failure_output}

    Standards: Load via state.cached_standards or WebFetch.
    Project rules: {project_rules_path}

    ## Multi-Tenant (Go only)
    Implement DUAL-MODE from the start. Use resolvers for all resources
    (tmcore.GetPGContext, tmcore.GetMBContext, etc.) — they work transparently
    in single-tenant and multi-tenant mode.
    Load multi-tenant.md for patterns.

    ## Your Task
    1. Implement minimum code to make tests pass
    2. Run tests — all must pass
    3. Write delivery verification results
    4. Commit with message: "{feat|fix|test|chore}(scope): description"

    ## Required Output
    - Implementation files created/modified
    - Test execution output (must show PASS)
    - Delivery verification: coverage %, files changed
    - Git commit SHA
```

## Step 5: Gate 0 Exit — Delivery Verification

After TDD-GREEN passes, verify delivery:

**Automated checks (run on all files changed by Gate 0):**

```bash
# A. File size (>1500 = FAIL, >1000 = PARTIAL unless cohesion justified)
find . -name "*.go" ! -name "*_test.go" ! -path "*/generated/*" \
  -exec wc -l {} + | awk '$1 > 1000'

# B. License headers
for f in $files_changed; do
  head -10 "$f" | grep -qiE 'copyright|licensed|spdx|license' || echo "MISSING: $f"
done

# C. Lint (go: golangci-lint; ts: eslint)
golangci-lint run ./... || echo "LINT FAILED"

# D. Migration safety (if SQL migrations changed)
# Check for blocking ops: ADD COLUMN NOT NULL without DEFAULT, DROP COLUMN,
# CREATE INDEX without CONCURRENTLY, ALTER COLUMN TYPE, TRUNCATE
```

**Verdict:**
- PASS: all requirements delivered, 0 dead code, all checks pass
- PARTIAL: some requirements delivered → list gaps, return to Gate 0
- FAIL: critical requirements missing → return to Gate 0 with explicit instructions

## Output Format

```markdown
## Implementation Summary
- unit_id, agent used, TDD phase results

## TDD Results
- RED: test file path + failure output
- GREEN: test pass output + coverage

## Files Changed
- List of created/modified files

## Delivery Verification
- Each requirement: DELIVERED or NOT DELIVERED
- Automated checks: PASS/FAIL per check

## Handoff to Next Gate
- files_changed list for Gate 1
- Verdict: PASS | PARTIAL | FAIL
```
