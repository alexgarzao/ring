---
name: ring:dev-chaos-testing
description: |
  Gate 7 of development cycle — ensures chaos tests exist using Toxiproxy to verify
  graceful degradation under connection loss, latency, and network partitions.
  Runs at TASK cadence.

trigger: |
  - Gate 7 (after integration testing)
  - Service has external dependencies
  - Verify graceful degradation under failure conditions

skip_when: |
  - Not inside a development cycle (ring:dev-cycle)
  - Service has no external dependencies
  - Task is documentation-only, configuration-only, or non-code
  - Frontend-only project with no backend service dependencies

sequence:
  after: [ring:dev-integration-testing]
  before: [ring:dev-goroutine-leak-testing]

related:
  complementary: [ring:dev-cycle, ring:qa-analyst]
---

# Chaos Testing (Gate 7)

All infrastructure fails eventually. Gate 7 verifies graceful degradation.

**Block conditions:**
- No chaos tests = FAIL
- Any dependency without failure test = FAIL
- Recovery not verified = FAIL
- System crashes on failure = FAIL

## Step 0: Auto-Detect Dependencies

Same logic as Gate 6 (integration testing). Scan docker-compose.yml and go.mod/package.json for postgres, mongodb, valkey, redis, rabbitmq.

If no external dependencies detected → SKIP (document reason).

## Step 1: Validate Input

Required: `unit_id` (TASK id), `language`, `implementation_files`, `gate0_handoffs`.
Optional: `external_dependencies`, `gate6_handoff`.

## Step 2: Dispatch QA Analyst (Chaos Mode)

```yaml
Task:
  subagent_type: "ring:qa-analyst"
  description: "Write chaos tests for {unit_id}"
  prompt: |
    ## Chaos Testing — Gate 7

    unit_id: {unit_id}
    language: {language}
    external_dependencies: {external_dependencies}
    implementation_files: {implementation_files}

    Standards: Load via cached_standards or WebFetch:
    https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/testing-chaos.md

    ## Requirements
    - Use Toxiproxy to inject failures (NOT mocks)
    - Test naming: TestIntegration_Chaos_{Component}_{Scenario}
    - Build tag: //go:build integration
    - Guard: if os.Getenv("CHAOS") != "1" { t.Skip() }
    - Verify RECOVERY after each failure (not just that failure doesn't crash)

    ## Scenarios per dependency
    PostgreSQL/MongoDB: connection_loss, high_latency (3s), connection_reset
    RabbitMQ: connection_loss, partition (publisher + consumer separated)
    Redis/Valkey: connection_loss, high_latency
    HTTP upstreams: timeout, 500_error, slow_response

    ## Go Template
    ```go
    //go:build integration

    func TestIntegration_Chaos_Postgres_ConnectionLoss(t *testing.T) {
      if os.Getenv("CHAOS") != "1" {
        t.Skip("skipping chaos test: set CHAOS=1 to run")
      }
      ctx := context.Background()
      // Start Toxiproxy
      // Start Postgres via testcontainers
      // Route through Toxiproxy
      // Test normal operation → PASS
      // Inject: toxiproxy.AddToxic("latency_upstream", "latency", ...)
      // Test degraded operation → circuit breaker opens or graceful error
      // Remove toxic
      // Test recovery → service resumes normal operation
    }
    ```

    ## Scenarios Table (MANDATORY output)
    | Dependency | Scenario | Test Function | Failure Response | Recovery Verified |

    ## Run command
    CHAOS=1 go test -tags=integration -v ./... -run TestIntegration_Chaos_
```

## Step 3: Validate Results

```
if all dependencies covered AND all scenarios pass AND recovery verified:
  → PASS → proceed to Gate 8

if any failure:
  → Re-dispatch with specific gaps
  → iterations++

if iterations >= 3:
  → Escalate to user
```

## Output Format

```markdown
## Chaos Testing Result
unit_id | result: PASS/SKIP/FAIL | iterations

## Scenarios Coverage
| Dependency | Scenario | Test | Recovery | Status |

## Skip Reason (if applicable)
{auto-detection result}

## Handoff
gate7_result: PASS | SKIP | ESCALATED
test_files: [list]
```
