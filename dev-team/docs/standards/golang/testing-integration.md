# Go Standards - Integration Testing

> **Module:** testing-integration.md | **Sections:** INT-1 to INT-15 | **Parent:** [index.md](index.md)

This module covers integration testing patterns, testcontainers usage, property-based testing, chaos testing, and anti-patterns for Go projects.

> **Gate Reference:** This module is loaded by `ring:qa-analyst` when `test_mode: integration` (Gate 3.5).

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| INT-1 | [Test Pyramid](#test-pyramid) | Unit > Integration > E2E ratio |
| INT-2 | [Decision Tree for Test Level](#decision-tree-for-test-level) | When to use integration tests |
| INT-3 | [File Naming Convention](#file-naming-convention-mandatory) | `*_integration_test.go` with build tags |
| INT-4 | [Function Naming Convention](#function-naming-convention-mandatory) | `TestIntegration_`, `TestProperty_`, `Fuzz` |
| INT-5 | [Build Tags](#build-tags-mandatory) | `//go:build integration` |
| INT-6 | [Testcontainers Patterns](#testcontainers-patterns-mandatory) | Container lifecycle management |
| INT-7 | [Parallel Test Prohibition](#parallel-test-prohibition-mandatory) | No `t.Parallel()` for integration tests |
| INT-8 | [Fixture Centralization](#fixture-centralization-mandatory) | `tests/utils/` organization |
| INT-9 | [Stub Centralization](#stub-centralization-mandatory) | `tests/utils/stubs/` patterns |
| INT-10 | [Property-Based Testing](#property-based-testing) | `testing/quick.Check` patterns |
| INT-11 | [Native Fuzz Testing](#native-fuzz-testing) | `Fuzz*` functions (Go 1.18+) |
| INT-12 | [Chaos Testing](#chaos-testing) | Toxiproxy patterns |
| INT-13 | [Logger Testing](#logger-testing) | Capturing and asserting log output |
| INT-14 | [Guardrails (11 Anti-Patterns)](#guardrails-11-anti-patterns-mandatory) | What not to do |
| INT-15 | [Test Failure Analysis](#test-failure-analysis-no-greenwashing) | Root cause tracking |

**Meta-sections (excluded from agent checks):** [Output Format (Integration Mode)](#output-format-integration-mode) | [Anti-Rationalization Table (Integration Testing)](#anti-rationalization-table-integration-testing)

---

## Test Pyramid

### Principle: Unit > Integration > E2E

| Level | Scope | Speed | Coverage Focus | Typical Ratio |
|-------|-------|-------|----------------|---------------|
| **Unit** | Single function/class | Fast (ms) | Business logic, edge cases | 70% |
| **Integration** | Multiple components + real I/O | Medium (s) | Database, APIs, services | 20% |
| **E2E** | Full system | Slow (min) | Critical user journeys | 10% |

**Default to unit tests.** Integration tests are for verifying boundaries work correctly.

### When Integration Tests Are Warranted

| Code Type | Integration Test Needed | What to Test |
|-----------|------------------------|--------------|
| Repository/Adapter | Touches DB (PostgreSQL, MongoDB, Redis) | CRUD, query correctness, constraints |
| Encryption | Round-trip encrypt → store → retrieve → decrypt | Data integrity after persistence |
| Indexes/Constraints | Unique indexes, partial filters, foreign keys | Constraint violations |
| Message Brokers | RabbitMQ publish/consume | Message delivery, acknowledgment |
| External Services | HTTP clients, gRPC clients | Connection handling, retry logic |
| Transactions | Multi-step DB operations | Rollback behavior, isolation |
| Migrations | Schema changes | Forward/backward compatibility |

### When Integration Tests Are NOT Needed

| Code Type | Unit Test Sufficient | Reason |
|-----------|---------------------|--------|
| Pure functions | Filter builders, validators, mappers | No I/O, deterministic |
| Business logic | Use case orchestration with mocked repos | Logic testable in isolation |
| HTTP handlers | With mocked services | HTTP behavior testable without real DB |
| Model transformations | Entity to DTO conversions | No external dependencies |

---

## Decision Tree for Test Level

```text
1. Does the code do real I/O? (network, file, DB, container)
   |
   +-- YES -> Integration test (*_integration_test.go, TestIntegration_)
   |
   +-- NO -> Continue to #2
             |
             2. Is this an HTTP handler?
             |
             +-- YES -> Component test (mock at repository level)
             |
             +-- NO -> Unit test (*_test.go)

3. Test technique?
   |
   +-- Verifying properties with testing/quick.Check? -> TestProperty_ prefix
   +-- Native Go fuzz (millions of iterations)? -> Fuzz prefix (unit only!)
   +-- Standard test cases? -> Regular Test prefix
```

### Pre-Flight Checklist (MANDATORY Before Writing Any Test)

- [ ] Searched for existing tests covering this scenario (avoid duplicates)
- [ ] Confirmed test level matches I/O requirements (see Decision Tree)
- [ ] File naming matches level (`*_test.go` vs `*_integration_test.go`)
- [ ] Build tag present if integration (`//go:build integration`)
- [ ] `t.Parallel()` planned for unit tests only (not integration)

---

## File Naming Convention (MANDATORY)

| Test Type | File Pattern | Build Tag |
|-----------|--------------|-----------|
| Unit | `*_test.go` | None |
| Integration | `*_integration_test.go` | `//go:build integration` |
| Benchmark | `*_benchmark_test.go` | None |

### Correct Pattern

```go
// File: internal/adapters/postgres/user_integration_test.go

//go:build integration

package postgres_test

import (
    "testing"
    // ...
)

func TestIntegration_UserRepository_Create(t *testing.T) {
    // ...
}
```

### FORBIDDEN Pattern

```go
// File: internal/adapters/postgres/user_test.go  // WRONG: missing _integration suffix

//go:build integration  // WRONG: build tag on non-integration file

package postgres_test

func TestUserRepository_Create(t *testing.T) {  // WRONG: missing TestIntegration_ prefix
    // Makes real DB calls but in unit test file
}
```

---

## Function Naming Convention (MANDATORY)

| Level | Pattern | Example |
|-------|---------|---------|
| Unit | `Test{Unit}_{Scenario}` | `TestCreateAccount_NotFound` |
| Integration | `TestIntegration_{Component}_{Scenario}` | `TestIntegration_BalanceRepo_Find` |
| Benchmark | `Benchmark{Function}` | `BenchmarkOperateBalances` |

### By Technique

| Technique | Pattern | Applies To | Example |
|-----------|---------|------------|---------|
| Fuzz (Native Go) | `Fuzz{Subject}_{Field}` | Unit only | `FuzzCreateOrganization_LegalName` |
| Property-Based | `TestProperty_{Subject}_{Scenario}` | Unit | `TestProperty_Organization_FieldLengths` |
| Property-Based | `TestIntegration_Property_{Subject}_{Scenario}` | Integration | `TestIntegration_Property_Account_DuplicateAlias` |
| Chaos | `TestIntegration_Chaos_{Component}_{Scenario}` | Integration only | `TestIntegration_Chaos_Redis_NetworkPartition` |

### Naming Rules

| Rule | Correct | Incorrect |
|------|---------|-----------|
| No "Success" suffix | `TestGetByID` (happy path) | `TestGetByIDSuccess` (redundant) |
| Use `_Suffix` for variants | `TestGetByID_NotFound` | `TestGetByIDNotFound` |
| Snake_case for table-driven | `{name: "not_found"}` | `{name: "NotFound"}` |

---

## Build Tags (MANDATORY)

**HARD GATE:** All integration test files MUST have `//go:build integration` at the top.

### Correct Pattern

```go
//go:build integration

package handler_test

import "testing"

func TestIntegration_UserHandler_Create(t *testing.T) {
    // ...
}
```

### Running Tests

```bash
# Run only unit tests (default; excludes files built with integration tag)
go test ./...

# Run only integration tests (files with //go:build integration)
go test -tags=integration ./...

# Run all tests (unit + integration): same as above; -tags=integration includes
# both unit tests and files built with the integration tag
go test -tags=integration ./...   # runs unit tests plus integration-tagged tests
```

### Detection Command

```bash
# Find integration tests without build tag (should return 0)
find . -name "*_integration_test.go" -exec grep -L "//go:build integration" {} \;
```

---

## Testcontainers Patterns (MANDATORY)

**HARD GATE:** Integration tests MUST use testcontainers for external dependencies. Real production services are FORBIDDEN.

### Container Setup Pattern

```go
//go:build integration

package postgres_test

import (
    "context"
    "testing"
    "time"

    "github.com/stretchr/testify/require"
    "github.com/testcontainers/testcontainers-go"
    "github.com/testcontainers/testcontainers-go/modules/postgres"
    "github.com/testcontainers/testcontainers-go/wait"
)

func TestIntegration_UserRepository_Create(t *testing.T) {
    ctx := context.Background()

    // Setup container with wait strategy
    postgresC, err := postgres.Run(ctx,
        "docker.io/postgres:16-alpine",
        postgres.WithDatabase("test_db"),
        postgres.WithUsername("test"),
        postgres.WithPassword("test"),
        testcontainers.WithWaitStrategy(
            wait.ForLog("database system is ready to accept connections").
                WithOccurrence(2).
                WithStartupTimeout(30*time.Second),
        ),
    )
    require.NoError(t, err)

    // Automatic cleanup
    t.Cleanup(func() {
        if err := postgresC.Terminate(ctx); err != nil {
            t.Logf("failed to terminate container: %v", err)
        }
    })

    // Get dynamic connection string (not hardcoded port!)
    connStr, err := postgresC.ConnectionString(ctx, "sslmode=disable")
    require.NoError(t, err)

    // Run test against real container
    repo := NewUserRepository(connStr)
    // ...
}
```

### Container Version Synchronization

**Versions MUST match `infra/docker-compose` exactly.**

| Service | docker-compose | Testcontainers |
|---------|----------------|----------------|
| PostgreSQL | `postgres:16-alpine` | `postgres:16-alpine` |
| Redis | `redis:7-alpine` | `redis:7-alpine` |
| MongoDB | `mongo:7.0` | `mongo:7.0` |
| RabbitMQ | `rabbitmq:3.12-management` | `rabbitmq:3.12-management` |

### Centralized Setup Helpers

Use `tests/utils/` for reusable container setup:

```go
// tests/utils/postgres/container.go
package pgtestutil

func SetupContainer(t *testing.T) *PostgresContainer {
    ctx := context.Background()

    postgresC, err := postgres.Run(ctx,
        "docker.io/postgres:16-alpine",
        // ... standard config
    )
    require.NoError(t, err)

    t.Cleanup(func() { postgresC.Terminate(ctx) })

    return &PostgresContainer{Container: postgresC}
}
```

Usage in tests:

```go
func TestIntegration_UserRepository(t *testing.T) {
    container := pgtestutil.SetupContainer(t)  // cleanup is automatic

    repo := NewUserRepository(container.ConnectionString())
    // ...
}
```

---

## Parallel Test Prohibition (MANDATORY)

**HARD GATE:** Integration tests MUST NOT use `t.Parallel()`. Container state is shared.

### FORBIDDEN Pattern

```go
//go:build integration

func TestIntegration_UserCreate(t *testing.T) {
    t.Parallel()  // FORBIDDEN: causes container flakiness
    // ...
}

func TestIntegration_UserUpdate(t *testing.T) {
    t.Parallel()  // FORBIDDEN: race condition with UserCreate
    // ...
}
```

### Correct Pattern

```go
//go:build integration

func TestIntegration_UserCreate(t *testing.T) {
    // No t.Parallel() - tests run sequentially
    // ...
}

func TestIntegration_UserUpdate(t *testing.T) {
    // No t.Parallel() - waits for UserCreate to complete
    // ...
}
```

### Detection Command

```bash
# Find t.Parallel() in integration tests (should return 0)
grep -rn "t\.Parallel()" --include="*_integration_test.go" .
```

### Why Sequential Execution

| Problem | Impact |
|---------|--------|
| Shared database state | Tests corrupt each other's data |
| Container resource limits | Parallel access causes timeouts |
| Determinism | Order-dependent results |
| Debugging | Cannot reproduce failures |

---

## Fixture Centralization (MANDATORY)

**HARD GATE:** All entity fixtures MUST be centralized in `tests/utils/<infra>/fixtures.go`. Local `createTest*` helpers are FORBIDDEN.

### Correct Pattern

```go
// tests/utils/postgres/fixtures.go
package pgtestutil

type AccountParams struct {
    Name      string
    Alias     string
    AssetCode string
    Balance   decimal.Decimal
}

func DefaultAccountParams() AccountParams {
    return AccountParams{
        Name:      "Test Account",
        Alias:     "@test",
        AssetCode: "USD",
        Balance:   decimal.NewFromInt(1000),
    }
}

func CreateTestAccount(t *testing.T, db *sql.DB, orgID, ledgerID string, params *AccountParams) string {
    t.Helper()

    if params == nil {
        p := DefaultAccountParams()
        params = &p
    }

    id := uuid.New().String()
    _, err := db.Exec(`
        INSERT INTO accounts (id, org_id, ledger_id, name, alias, asset_code, balance)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    `, id, orgID, ledgerID, params.Name, params.Alias, params.AssetCode, params.Balance)
    require.NoError(t, err)

    t.Cleanup(func() {
        db.Exec("DELETE FROM accounts WHERE id = $1", id)
    })

    return id
}

// Simple variant for common cases
func CreateTestAccountSimple(t *testing.T, db *sql.DB, orgID, ledgerID, name string) string {
    params := DefaultAccountParams()
    params.Name = name
    return CreateTestAccount(t, db, orgID, ledgerID, &params)
}
```

### Usage in Tests

```go
func TestIntegration_AccountRepository_Find(t *testing.T) {
    container := pgtestutil.SetupContainer(t)

    // Use centralized fixtures
    params := pgtestutil.DefaultAccountParams()
    params.Alias = "@custom-alias"
    accountID := pgtestutil.CreateTestAccount(t, container.DB, orgID, ledgerID, &params)

    // Test
    account, err := repo.Find(ctx, accountID)
    require.NoError(t, err)
    assert.Equal(t, "@custom-alias", account.Alias)
}
```

### FORBIDDEN Pattern

```go
// Inside test file - FORBIDDEN
func createTestAccount(name string) *mmodel.Account {
    return &mmodel.Account{Name: testutils.Ptr(name)}
}

func TestIntegration_Something(t *testing.T) {
    account := createTestAccount("test")  // WRONG: local helper
}
```

---

## Stub Centralization (MANDATORY)

**HARD GATE:** All stubs for external dependencies MUST be centralized in `tests/utils/stubs/`.

### Stubs vs Mocks

| Type | Location | When to Use |
|------|----------|-------------|
| **Stubs** | `tests/utils/stubs/` | Fixed behavior, dependency "just works" |
| **Mocks** | Generated by gomock | Verify specific interactions |

### Stub Pattern

```go
// tests/utils/stubs/ports.go
package stubs

// BalancePortStub provides a simple stub that always succeeds
type BalancePortStub struct {
    CreateBalanceFunc func(ctx context.Context, balance *mmodel.Balance) (*mmodel.Balance, error)
}

func (s *BalancePortStub) CreateBalanceSync(ctx context.Context, balance *mmodel.Balance) (*mmodel.Balance, error) {
    if s.CreateBalanceFunc != nil {
        return s.CreateBalanceFunc(ctx, balance)
    }
    // Default: return the input with generated ID
    balance.ID = uuid.New().String()
    return balance, nil
}

// LoggerStub captures log messages for assertion
type LoggerStub struct {
    warnings []string
    errors   []string
    infos    []string
}

func (l *LoggerStub) Warnf(template string, args ...interface{}) {
    l.warnings = append(l.warnings, fmt.Sprintf(template, args...))
}

func (l *LoggerStub) HasWarning(substring string) bool {
    for _, w := range l.warnings {
        if strings.Contains(w, substring) {
            return true
        }
    }
    return false
}

func (l *LoggerStub) WarningCount() int {
    return len(l.warnings)
}

func (l *LoggerStub) Reset() {
    l.warnings = nil
    l.errors = nil
    l.infos = nil
}
```

### Usage in Tests

```go
import "github.com/LerianStudio/midaz/v3/tests/utils/stubs"

func TestUseCase_CreateAccount(t *testing.T) {
    commandUC := &command.UseCase{
        BalancePort: &stubs.BalancePortStub{},  // Stub: always succeeds
    }

    result, err := commandUC.CreateAccount(ctx, input)
    require.NoError(t, err)
}
```

---

## Property-Based Testing

Property-based tests verify **invariant properties** hold across multiple inputs. Use `testing/quick.Check`.

### Pattern

```go
import "testing/quick"

func TestProperty_FullJitter_AlwaysPositive(t *testing.T) {
    err := quick.Check(func(duration time.Duration) bool {
        // PROPERTY: Jitter is always non-negative
        return FullJitter(duration) >= 0
    }, nil)
    require.NoError(t, err)
}

func TestProperty_Organization_FieldLengths(t *testing.T) {
    err := quick.Check(func(name string, code string) bool {
        if len(name) > 256 || len(code) > 10 {
            return true // Skip unrealistic inputs
        }

        org, err := NewOrganization(name, code)
        if err != nil {
            // PROPERTY: Validation errors are returned, never panic
            return true
        }

        // PROPERTY: Valid organizations have non-empty ID
        return org.ID != ""
    }, nil)
    require.NoError(t, err)
}
```

### When to Use Property-Based vs Table-Driven

| Use Property-Based When | Use Table-Driven When |
|-------------------------|----------------------|
| Testing invariants across many inputs | Testing specific known scenarios |
| Verifying "never panics" guarantees | Testing error messages |
| Mathematical properties | Testing specific edge cases |
| Input validation exhaustiveness | Documenting expected behavior |

---

## Native Fuzz Testing

**Native fuzz tests MUST be unit-level only** - requires fast execution (millions of iterations).

### Fuzz Function Pattern

```go
func FuzzCreateOrganization_LegalName(f *testing.F) {
    // Seed corpus with edge cases
    f.Add("Acme, Inc.")                // valid
    f.Add("")                          // empty
    f.Add("a]]]a")                     // unicode
    f.Add("<script>alert(1)</script>") // XSS
    f.Add(strings.Repeat("x", 1000))   // long

    f.Fuzz(func(t *testing.T, name string) {
        // Bound input length to prevent resource exhaustion
        if len(name) > 512 {
            name = name[:512]
        }

        // PROPERTY: No panic, no 5xx errors
        result, err := ValidateOrganizationName(name)
        if err == nil {
            assert.NotEmpty(t, result)
        }
        // No panic = test passes
    })
}
```

### Supported Fuzz Input Types

| Primitive Types | Numeric Types |
|-----------------|---------------|
| `string`, `[]byte`, `bool` | `int`, `int8`, `int16`, `int32`, `int64` |
| | `uint`, `uint8`, `uint16`, `uint32`, `uint64` |
| | `float32`, `float64` |

For complex types, use `[]byte` + JSON:

```go
f.Fuzz(func(t *testing.T, data []byte) {
    var input MyStruct
    if json.Unmarshal(data, &input) != nil {
        return // Skip invalid JSON
    }
    // Test with valid struct
})
```

### Seed Corpus Categories

| Category | Examples |
|----------|----------|
| Valid inputs | `"Acme, Inc."`, `"100.00"`, `"user@example.com"` |
| Edge cases | `""`, `"a"`, max length strings |
| Unicode/encoding | Greek, Japanese, emoji |
| Invalid formats | `"{ invalid json }"`, `"not-a-number"` |
| Security payloads | `"<script>"`, `"' OR 1=1"`, null bytes |
| Boundary values | `"9223372036854775807"` (max int64) |

---

## Chaos Testing

Tests system behavior under failure conditions. **Integration only.**

### Dual-Gate Pattern

```go
//go:build integration

func TestIntegration_Chaos_Redis_ConnectionLoss(t *testing.T) {
    // Gate 1: Chaos tests disabled by default
    if os.Getenv("CHAOS") != "1" {
        t.Skip("Chaos tests disabled (set CHAOS=1)")
    }

    // Gate 2: Skip in short mode
    if testing.Short() {
        t.Skip("Skipping chaos test in short mode")
    }

    // Setup
    redisC := redistestutil.SetupContainer(t)
    proxy := chaosutil.SetupToxiproxy(t, redisC)

    // 1. Verify normal operation
    client := redis.NewClient(proxy.ListenAddr())
    err := client.Set(ctx, "key", "value", 0).Err()
    require.NoError(t, err)

    // 2. Inject failure
    err = proxy.Disconnect()
    require.NoError(t, err)

    // 3. Verify expected failure behavior
    err = client.Set(ctx, "key2", "value2", 0).Err()
    require.Error(t, err) // Should fail gracefully

    // 4. Restore
    err = proxy.Reconnect()
    require.NoError(t, err)

    // 5. Verify recovery
    err = client.Set(ctx, "key3", "value3", 0).Err()
    require.NoError(t, err)
}
```

### Chaos Test Infrastructure

Location: `tests/utils/chaos/`

```go
// tests/utils/chaos/toxiproxy.go
package chaosutil

type ToxiproxyWrapper struct {
    proxy *toxiproxy.Proxy
}

func (t *ToxiproxyWrapper) Disconnect() error {
    return t.proxy.Disable()
}

func (t *ToxiproxyWrapper) Reconnect() error {
    return t.proxy.Enable()
}

func (t *ToxiproxyWrapper) AddLatency(latency time.Duration) error {
    _, err := t.proxy.AddToxic("latency", "latency", "", 1, toxiproxy.Attributes{
        "latency": latency.Milliseconds(),
    })
    return err
}
```

### Running Chaos Tests

```bash
# Run chaos tests
CHAOS=1 go test -tags=integration -v ./tests/chaos/...

# Skip chaos tests (default)
go test -tags=integration ./...
```

---

## Logger Testing

### Default: Use Real Logger

Most tests don't need to verify log output:

```go
import libZap "github.com/LerianStudio/lib-commons/v2/commons/zap"

func TestSomething(t *testing.T) {
    logger := libZap.InitializeLogger()
    // use logger in test setup
}
```

### Exception: LoggerStub for Verification

Use when verifying log messages is the test objective:

```go
import "github.com/LerianStudio/midaz/v3/tests/utils/stubs"

func TestFunction_LogsDeprecationWarning(t *testing.T) {
    logger := &stubs.LoggerStub{}

    result := FunctionUnderTest(logger)

    assert.True(t, logger.HasWarning("DEPRECATED"))
    assert.Equal(t, 1, logger.WarningCount())
}
```

| Scenario | Use |
|----------|-----|
| Logger is just a dependency | Real logger |
| Verify warning/error was logged | `stubs.LoggerStub{}` |
| Verify deprecation messages | `stubs.LoggerStub{}` |
| Debugging test failures | Real logger |

---

## Guardrails (11 Anti-Patterns) (MANDATORY)

**HARD GATE:** Before completing any integration test, verify NONE of these anti-patterns exist.

| # | Anti-Pattern | Detection | Why Wrong | Correct Pattern |
|---|--------------|-----------|-----------|-----------------|
| 1 | **Hardcoded ports** | `grep -rn ":5432\|:6379\|:27017"` | Port conflicts in CI | Use testcontainers dynamic ports |
| 2 | **Shared database state** | Tests depend on prior test data | Flaky tests | Each test creates own data |
| 3 | **Missing cleanup** | No `t.Cleanup()` | Resource leaks | Always use `t.Cleanup()` |
| 4 | **Sleep-based waits** | `grep "time.Sleep"` | Slow, unreliable | Use wait strategies |
| 5 | **Production database** | env var pointing to real DB | Data corruption | Always use containers |
| 6 | **Missing build tag** | `//go:build integration` absent | Tests run with unit tests | Always add build tag |
| 7 | **t.Parallel() usage** | `grep "t.Parallel()"` | State conflicts | Remove all `t.Parallel()` calls from integration tests |
| 8 | **Hardcoded credentials** | `"postgres:password@"` in code | Security risk | Use containers default creds |
| 9 | **Network-dependent tests** | Tests call external APIs | Flaky, slow | Mock or use testcontainers |
| 10 | **Missing timeout** | No `context.WithTimeout` | Tests hang forever | Always set timeout |
| 11 | **Greenwashing failures** | Ignoring intermittent failures | Hidden bugs | Track and fix all failures |

### Detection Script

```bash
#!/bin/bash
# detect-integration-antipatterns.sh

echo "Checking for integration test anti-patterns..."

# 1. Hardcoded ports
echo "1. Hardcoded ports:"
grep -rn ":5432\|:6379\|:27017\|:5672" --include="*_integration_test.go" . | grep -v "// allowed:" || echo "   None found"

# 2. t.Parallel() in integration tests
echo "2. t.Parallel() usage:"
grep -rn "t\.Parallel()" --include="*_integration_test.go" . || echo "   None found"

# 3. Missing build tags
echo "3. Missing build tags:"
find . -name "*_integration_test.go" -exec grep -L "//go:build integration" {} \; || echo "   None found"

# 4. time.Sleep usage
echo "4. time.Sleep usage:"
grep -rn "time\.Sleep" --include="*_integration_test.go" . || echo "   None found"

# 5. os.Setenv instead of t.Setenv
echo "5. os.Setenv usage:"
grep -rn "os\.Setenv" --include="*_integration_test.go" . || echo "   None found"
```

### Additional Guardrails

| # | Guardrail | Enforcement |
|---|-----------|-------------|
| 12 | **TestProperty_ prefix reserved** | Only for `testing/quick.Check` tests |
| 13 | **Empty test templates** | No `// TODO: Add test cases` |
| 14 | **Duplicate tests** | Consolidate into table-driven |
| 15 | **Clean imports** | Remove unused imports after refactoring |
| 16 | **Non-idiomatic string construction** | Use `fmt.Sprintf`, not `string(rune(...))` |
| 17 | **Import alias consistency** | Use `testutils` alias consistently |
| 18 | **Loop variable capture** | Capture `tc := tc` before subtest closure |
| 19 | **Chaos test error handling** | Check errors from `proxy.Disconnect()/Reconnect()` |
| 20 | **Shared test utilities** | Use `testutils.Ptr()`, not local helpers |

---

## Test Failure Analysis (No Greenwashing)

**HARD GATE:** Never weaken tests to make them pass.

### Decision Tree

```text
Test failed -> Is the assertion correct?
              |
              +-- NO (test bug) -> Fix the test, document why
              |
              +-- YES -> Is the implementation correct?
                         |
                         +-- NO (app bug) -> Keep test RED, report bug
                         |
                         +-- UNCLEAR -> Investigate further
```

### Rules

| Situation | Action |
|-----------|--------|
| Test is wrong | Fix test, explain the mistake |
| App has bug | **Keep test failing**, document bug |
| Unclear | Investigate more, ask if needed |

### Bug Report Format

```markdown
BUG IDENTIFIED (not test error):
- Location: internal/services/command/create-account.go:45
- Issue: Duplicate key error not mapped to EntityConflictError
- Impact: API returns 500 instead of 409 for duplicate aliases

-> Keeping test RED. Fix required in application code.
```

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Test is too strict" | Strict tests catch bugs early | **Keep the assertion** |
| "Works in production" | Production may have hidden bugs | **Trust the test** |
| "Intermittent failure" | Flaky = broken. Fix the root cause. | **Fix the test or code** |
| "Edge case won't happen" | Edge cases cause production incidents | **Keep edge case tests** |
| "Time pressure" | Shipping bugs costs more than fixing tests | **Fix before merge** |

---

## Integration Test Quality Gate Checklist

**Before marking integration tests complete:**

- [ ] All files named `*_integration_test.go`
- [ ] All files have `//go:build integration` tag
- [ ] All functions named `TestIntegration_*`
- [ ] No `t.Parallel()` in any integration test
- [ ] All containers use testcontainers (no production deps)
- [ ] All containers have `t.Cleanup()` for termination
- [ ] No hardcoded ports (use dynamic ports from containers)
- [ ] No `time.Sleep()` (use wait strategies)
- [ ] All fixtures from `tests/utils/`, no local helpers
- [ ] All stubs from `tests/utils/stubs/`, no local mocks
- [ ] Anti-pattern detection script passes
- [ ] Tests pass 3x consecutively (no flaky tests)

---

## Output Format (Integration Mode)

When `ring:qa-analyst` runs in integration mode, output:

```markdown
## VERDICT: PASS/FAIL

## Integration Testing Summary
| Metric | Value |
|--------|-------|
| Scenarios tested | X |
| Tests written | Y |
| Tests passed | Y |
| Tests failed | 0 |
| Flaky tests detected | 0 |

## Scenario Coverage
| Scenario | Test File | Tests | Status |
|----------|-----------|-------|--------|
| Database CRUD | user_integration_test.go | 5 | PASS |
| Message Queue | queue_integration_test.go | 3 | PASS |

## Quality Gate Results
| Check | Status | Evidence |
|-------|--------|----------|
| Build tags present | PASS | All files have //go:build integration |
| No hardcoded ports | PASS | 0 matches |
| Testcontainers used | PASS | postgres, redis containers |
| No t.Parallel() | PASS | 0 matches |
| Cleanup present | PASS | All containers have t.Cleanup() |
| Anti-pattern scan | PASS | 0 violations |

## Next Steps
- Ready for Gate 4 (Review): YES
```

---

## Anti-Rationalization Table (Integration Testing)

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Unit tests cover this" | Unit tests mock dependencies | **Write integration tests** |
| "Testcontainers is slow" | Speed < correctness | **Use testcontainers** |
| "Database tests are fragile" | Fragile = poorly written | **Fix test isolation** |
| "CI doesn't have Docker" | CI without Docker = broken CI | **Enable Docker in CI** |
| "No time for integration tests" | Integration bugs cost 10x more | **Write integration tests** |
| "t.Parallel() makes tests faster" | Faster but flaky | **Remove t.Parallel()** |
| "Local helpers are convenient" | Convenience causes duplication | **Use tests/utils/** |
| "This failure is intermittent" | Intermittent = broken | **Fix root cause** |
