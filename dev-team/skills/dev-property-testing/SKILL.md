---
name: ring:dev-property-testing
description: |
  Gate 5 of development cycle — ensures property-based tests exist to verify
  domain invariants hold for all randomly generated inputs (testing/quick package for Go).

trigger: |
  - Gate 5 (after fuzz testing)
  - Backend tasks with domain logic containing invariants

skip_when: |
  - Not inside a development cycle (ring:dev-cycle)
  - Task is documentation-only, configuration-only, or non-code
  - No domain logic with invariants was added or modified
  - Frontend-only project

sequence:
  after: [ring:dev-fuzz-testing]
  before: [ring:dev-integration-testing]

related:
  complementary: [ring:dev-cycle, ring:qa-analyst]
---

# Property-Based Testing (Gate 5)

Unit tests verify specific examples. Property tests verify invariants across all inputs.

Examples of domain invariants:
- Balance is never negative
- Account IDs are always unique
- Debit + Credit entries always balance
- Currency conversions are reversible

**Block conditions:**
- Domain with invariants but no property tests = FAIL
- Property test doesn't cover the invariant = FAIL

## Step 1: Validate Input

Required: `unit_id` (TASK id), `language` (go), `implementation_files`, `gate0_handoffs`.
Optional: `domain_invariants`, `gate4_handoff`.

## Step 2: Identify Domain Invariants

If `domain_invariants` not provided, dispatch `ring:codebase-explorer` to identify:

```
Scan implementation_files for:
- Domain entities with constraints (min/max values, non-null fields)
- Business rules with "always", "never", "must", "cannot"
- Mathematical relationships (sum, balance, totals)
- Ordering properties (created_at < updated_at)
- Uniqueness constraints
Output: list of testable invariants with property description
```

If no invariants found → SKIP (document reason).

## Step 3: Dispatch QA Analyst

```yaml
Task:
  subagent_type: "ring:qa-analyst"
  description: "Write property-based tests for {unit_id}"
  prompt: |
    ## Property-Based Testing — Gate 5

    unit_id: {unit_id}
    language: {language}
    domain_invariants: {invariants}
    implementation_files: {implementation_files}

    Standards: Load via cached_standards or WebFetch Ring testing standards.

    ## Go: testing/quick package
    ```go
    import "testing/quick"

    func TestProperty_{InvariantName}(t *testing.T) {
      property := func({args with types}) bool {
        // setup
        result, err := domain.{Operation}({args})
        if err != nil {
          return true // valid error is ok
        }
        // verify invariant
        return {invariant_condition}
      }
      if err := quick.Check(property, &quick.Config{MaxCount: 1000}); err != nil {
        t.Errorf("invariant violated: %v", err)
      }
    }
    ```

    ## Invariants to Test
    For each invariant in domain_invariants:
    - Write a property function that returns bool (true = invariant holds)
    - Use quick.Config{MaxCount: 1000} for thorough testing
    - Include specific counter-examples in error messages

    ## Invariants Coverage Table (MANDATORY)
    | Invariant | Property Function | MaxCount | Status |

    ## Required Output
    - Test files with property tests
    - go test -v output showing all properties pass
    - Invariants coverage table
```

## Step 4: Validate Results

```
if all invariants covered AND all properties pass:
  → PASS → proceed to Gate 6

if any invariant without test OR property violation found:
  → Re-dispatch with gaps
  → iterations++
```

## Output Format

```markdown
## Property Testing Result
unit_id | result: PASS/SKIP/FAIL | iterations

## Invariants Coverage
| Invariant | Property | MaxCount | Violations Found | Status |

## Skip Reason (if applicable)
{no domain invariants found in: files}

## Handoff
gate5_result: PASS | SKIP | ESCALATED
test_files: [list]
```
