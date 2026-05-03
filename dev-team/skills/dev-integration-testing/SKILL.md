---
name: ring:dev-integration-testing
description: |
  Gate 6 of development cycle — ensures integration tests pass for all external
  dependency interactions using real containers via testcontainers. Runs at TASK
  cadence (after all subtasks complete Gate 0 + Gate 3 + Gate 9).

trigger: |
  - Gate 6 of development cycle (after property-based testing)
  - Service has external dependencies (database, cache, queue, external API)

skip_when: |
  - Not inside a development cycle (ring:dev-cycle)
  - Task is documentation-only, configuration-only, or non-code
  - Service has no external dependencies (verified by auto-detection, not assumed)
  - Pure library package with no integration points

sequence:
  after: [ring:dev-property-testing]
  before: [ring:dev-chaos-testing]

related:
  complementary: [ring:dev-cycle, ring:qa-analyst]
---

# Integration Testing (Gate 6)

Unit tests mock. Integration tests verify real behavior. Both required.

**Block conditions:**
- Any integration scenario without test = FAIL
- Any test using production services = FAIL
- Any test with hardcoded ports = FAIL
- Any flaky test (fails on retry) = FAIL

## Step 0: Auto-Detect External Dependencies

When `external_dependencies` is empty or not provided, scan codebase:

```
docker-compose.yml: grep for postgres, mongodb, valkey, redis, rabbitmq
go.mod: pgx/lib-pq → postgres, mongo-driver → mongodb, valkey-go/go-redis → redis/valkey, amqp091-go → rabbitmq
package.json: pg/prisma → postgres, mongodb/mongoose → mongodb, redis/ioredis → redis, amqplib → rabbitmq
```

Set `external_dependencies` = deduplicated list. If still empty after scan → Gate 6 SKIP.

## Step 1: Validate Input

Required: `unit_id` (TASK id, not subtask), `language`, `implementation_files`, `gate0_handoffs`.
Optional: `integration_scenarios`, `external_dependencies`, `gate3_handoff`.

If `integration_scenarios` empty AND `external_dependencies` empty (after auto-detect) → SKIP (document reason).

## Step 2: Dispatch QA Analyst (Integration Mode)

```yaml
Task:
  subagent_type: "ring:qa-analyst"
  description: "Write integration tests for {unit_id}"
  prompt: |
    ## Integration Testing — Gate 6

    unit_id: {unit_id}
    language: {language}
    external_dependencies: {external_dependencies}
    integration_scenarios: {integration_scenarios}
    implementation_files: {implementation_files}

    Standards: Load via cached_standards or WebFetch Ring testing standards.

    ## Rules
    - Use testcontainers for ALL external services (never assume running instances)
    - Never hardcode ports — use container-assigned ports
    - Tag tests: `//go:build integration` or `describe.skip` (run separately)
    - Test must be idempotent (run 3x, all pass)
    - Clean up containers in t.Cleanup or afterAll

    ## Go Template
    ```go
    //go:build integration

    func TestIntegration_{Scenario}(t *testing.T) {
      if testing.Short() {
        t.Skip("skipping integration test")
      }
      ctx := context.Background()
      // Start container
      container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{...})
      require.NoError(t, err)
      t.Cleanup(func() { container.Terminate(ctx) })
      // Get dynamic port
      host, _ := container.Host(ctx)
      port, _ := container.MappedPort(ctx, "5432/tcp")
      // Test assertions
    }
    ```

    ## Traceability Matrix (MANDATORY)
    | Scenario | Test Function | Container | Status |

    ## Required Output
    - Test files with build tags
    - Run command: `go test -tags=integration -v ./...`
    - Test results (3 runs, all PASS)
    - Traceability matrix
```

## Step 3: Validate Results

```
if all scenarios covered AND all tests pass (3 runs) AND no hardcoded ports:
  → PASS → proceed to Gate 7

if any failure:
  → Re-dispatch with explicit gaps
  → iterations++

if iterations >= 3:
  → Escalate to user
```

## Output Format

```markdown
## Integration Testing Result
unit_id | result: PASS/SKIP/FAIL | iterations

## Scenarios Covered
| Scenario | Test | Container | Runs | Status |

## Skip Reason (if applicable)
{reason from auto-detection or explicit skip}

## Handoff to Next Gate
gate6_result: PASS | SKIP | ESCALATED
test_files: [list]
```
