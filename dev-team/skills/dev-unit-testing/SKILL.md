---
name: ring:dev-unit-testing
description: |
  Gate 3 of development cycle — ensures unit test coverage meets 85%+ threshold
  for all acceptance criteria using TDD methodology.

trigger: |
  - Gate 3 of development cycle
  - After Gates 0, 1, 2 complete
  - Need to verify implementation meets requirements via unit tests

skip_when: |
  - Not inside a development cycle (ring:dev-cycle)
  - Task is documentation-only, configuration-only, or non-code
  - No code implementation was produced
  - Changes limited to CI/CD, infrastructure, or deployment configuration

sequence:
  after: [ring:dev-implementation, ring:dev-devops, ring:dev-sre]
  before: [ring:codereview]

related:
  complementary: [ring:test-driven-development, ring:qa-analyst]

output_schema:
  metrics:
    result: PASS | FAIL | NEEDS_FIXES
    coverage_actual: float
    coverage_threshold: float
    tests_written: integer
    criteria_covered: "X/Y"
    iterations: integer
---

# Unit Testing (Gate 3)

Every acceptance criterion must have at least one executable unit test. Coverage threshold: **85%** minimum (PROJECT_RULES.md can raise, not lower).

## Step 1: Validate Input

Required: `unit_id`, `acceptance_criteria` (non-empty), `implementation_files` (non-empty), `language`.
Optional: `coverage_threshold` (default 85.0), `gate0_handoff`, `existing_tests`.

Reject `coverage_threshold < 85` — use 85% instead.

## Step 2: Dispatch QA Analyst

```yaml
Task:
  subagent_type: "ring:qa-analyst"
  description: "Write unit tests for {unit_id}"
  prompt: |
    ## Write Unit Tests

    unit_id: {unit_id}
    language: {language}
    coverage_threshold: {coverage_threshold}%
    acceptance_criteria: {acceptance_criteria}
    implementation_files: {implementation_files}

    Standards: Load via cached_standards or WebFetch Ring quality standards.

    ## Traceability Matrix (MANDATORY)
    Map every AC to at least one test:
    | AC-N | Test Function | File | Coverage |

    ## Go: Goroutine Leak Detection (MANDATORY if goroutines present)
    1. Scan for `go func()`, `go methodCall()`, `for range channel`, worker pools
    2. If goroutines found: add `goleak.VerifyNone(t)` to all test packages with goroutines
    3. Pattern:
       func TestMain(m *testing.M) {
         goleak.VerifyTestMain(m)
       }
    4. Report: goroutine_files count, goleak_coverage "X/Y packages", leaks_detected

    ## Go Standards
    - Table-driven tests (`tests := []struct{...}`)
    - Subtests: `t.Run(tc.name, func(t *testing.T))`
    - Use testify/assert, not raw `if` checks
    - Test naming: `Test{FunctionName}_{Scenario}_{ExpectedBehavior}`

    ## TypeScript Standards
    - describe/it blocks with meaningful names
    - Use jest/vitest matchers
    - Mock external dependencies

    ## Required Output
    - Test files created/modified
    - Coverage command + actual output (must show % ≥ threshold)
    - Traceability matrix (all ACs covered)
    - Goroutine verdict (Go only): PASS | NEEDS_ACTION | FAIL
```

## Step 3: Validate Output

```
if coverage_actual >= coverage_threshold AND all ACs covered:
  → PASS → proceed to Gate 4

if coverage_actual < coverage_threshold OR any AC uncovered:
  → Re-dispatch with explicit gap list
  → iterations++

if iterations >= 3:
  → Escalate to user
```

**Gate conditions:**
- Coverage below threshold = FAIL
- Any AC without test = FAIL
- (Go) goroutine leak detected = NEEDS_ACTION (dispatch fix before proceeding)

## Output Format

```markdown
## Validation Result
unit_id | result: PASS/FAIL | iterations | coverage: X%

## Traceability Matrix
| AC-N | Test Function | File | Status |

## Goroutine Analysis (Go only)
- Files with goroutines: N
- goleak coverage: X/Y packages
- Leaks detected: N
- Verdict: PASS | NEEDS_ACTION | FAIL

## Files Changed
[list]

## Handoff to Next Gate
gate3_result: PASS | ESCALATED
test_files: [list]
```
