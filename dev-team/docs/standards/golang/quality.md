# Go Standards - Quality

> **Module:** quality.md | **Sections:** §14-16 | **Parent:** [index.md](index.md)

This module covers testing, logging, and linting standards.

---

## Testing

### Table-Driven Tests (MANDATORY)

```go
func TestCreateUser(t *testing.T) {
    tests := []struct {
        name    string
        input   CreateUserInput
        want    *User
        wantErr error
    }{
        {
            name:  "valid user",
            input: CreateUserInput{Name: "John", Email: "john@example.com"},
            want:  &User{Name: "John", Email: "john@example.com"},
        },
        {
            name:    "invalid email",
            input:   CreateUserInput{Name: "John", Email: "invalid"},
            wantErr: ErrInvalidEmail,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := CreateUser(tt.input)

            if tt.wantErr != nil {
                require.ErrorIs(t, err, tt.wantErr)
                return
            }

            require.NoError(t, err)
            assert.Equal(t, tt.want.Name, got.Name)
        })
    }
}
```

### Test Naming Convention

```text
Test{Unit}_{Scenario}_{ExpectedResult}

Examples:
- TestOrderService_CreateOrder_WithValidItems_ReturnsOrder
- TestOrderService_CreateOrder_WithEmptyItems_ReturnsError
- TestMoney_Add_SameCurrency_ReturnsSum
```

### Edge Case Coverage (MANDATORY)

**Every acceptance criterion MUST have edge case tests beyond the happy path.**

| AC Type | Required Edge Cases | Minimum Count |
|---------|---------------------|---------------|
| Input validation | nil, empty string, boundary values, invalid format, special chars, max length | 3+ |
| CRUD operations | not found, duplicate key, concurrent modification, large payload | 3+ |
| Business logic | zero value, negative numbers, overflow, boundary conditions, invalid state | 3+ |
| Error handling | context timeout, connection refused, invalid response, retry exhausted | 2+ |
| Authentication | expired token, invalid signature, missing claims, revoked token | 2+ |

**Table-Driven Edge Cases Pattern:**

```go
func TestUserService_CreateUser(t *testing.T) {
    tests := []struct {
        name    string
        input   CreateUserInput
        wantErr error
    }{
        // Happy path
        {name: "valid user", input: validInput(), wantErr: nil},
        
        // Edge cases (MANDATORY - minimum 3)
        {name: "nil input", input: CreateUserInput{}, wantErr: ErrInvalidInput},
        {name: "empty email", input: CreateUserInput{Name: "John", Email: ""}, wantErr: ErrEmailRequired},
        {name: "invalid email format", input: CreateUserInput{Name: "John", Email: "invalid"}, wantErr: ErrInvalidEmail},
        {name: "email too long", input: CreateUserInput{Name: "John", Email: strings.Repeat("a", 256) + "@test.com"}, wantErr: ErrEmailTooLong},
        {name: "name with special chars", input: CreateUserInput{Name: "<script>", Email: "test@test.com"}, wantErr: ErrInvalidName},
    }
    // ... test execution
}
```

**Anti-Pattern (FORBIDDEN):**

```go
// ❌ WRONG: Only happy path
func TestUserService_CreateUser(t *testing.T) {
    result, err := service.CreateUser(validInput())
    require.NoError(t, err)  // No edge cases = incomplete test
}
```

### Mock Generation (GoMock - MANDATORY)

```go
// GoMock is the MANDATORY mock framework for all Go projects
//go:generate mockgen -source=repository.go -destination=mocks/mock_repository.go -package=mocks

// For interface in external package:
//go:generate mockgen -destination=mocks/mock_service.go -package=mocks github.com/example/pkg Service
```

### Benchmark Tests (b.Loop - MANDATORY for Go 1.24+)

**HARD GATE:** All benchmark tests MUST use `b.Loop()` instead of manual `for i := 0; i < b.N; i++` loops.

#### Why b.Loop Is MANDATORY

| Benefit | Explanation |
|---------|-------------|
| **Cleaner syntax** | `for b.Loop()` vs `for i := 0; i < b.N; i++` |
| **Compiler optimization** | Better optimizations with `b.Loop()` |
| **Official pattern** | Go 1.24+ standard |
| **Prevents errors** | No off-by-one errors with b.N |

#### Correct Pattern (REQUIRED - Go 1.24+)

```go
// ✅ CORRECT: Use b.Loop() (Go 1.24+)
func BenchmarkCreateUser(b *testing.B) {
    svc := setupService()

    for b.Loop() {
        _, err := svc.CreateUser(context.Background(), validInput)
        if err != nil {
            b.Fatal(err)
        }
    }
}

// ✅ CORRECT: With setup/teardown
func BenchmarkProcessOrder(b *testing.B) {
    b.ResetTimer()

    for b.Loop() {
        result := ProcessOrder(order)
        _ = result
    }
}

// ✅ CORRECT: With sub-benchmarks
func BenchmarkEncryption(b *testing.B) {
    b.Run("AES256", func(b *testing.B) {
        for b.Loop() {
            Encrypt(data, key)
        }
    })

    b.Run("RSA2048", func(b *testing.B) {
        for b.Loop() {
            EncryptRSA(data, key)
        }
    })
}
```

#### FORBIDDEN Pattern (Deprecated)

```go
// ❌ FORBIDDEN: Manual for loop (deprecated in Go 1.24+)
func BenchmarkOldPattern(b *testing.B) {
    for i := 0; i < b.N; i++ {  // WRONG: use b.Loop() instead
        DoSomething()
    }
}

// ❌ FORBIDDEN: Using loop variable unnecessarily
func BenchmarkOldPattern(b *testing.B) {
    for n := 0; n < b.N; n++ {  // WRONG: n is unused
        DoSomething()
    }
}
```

#### Detection Command

```bash
# Find old-style benchmarks (should return 0 matches)
grep -rn "for.*<.*b\.N" --include="*_test.go" ./internal ./pkg

# Should use b.Loop() instead
```

#### Migration Example

```go
// Before (Go < 1.24)
func BenchmarkOld(b *testing.B) {
    for i := 0; i < b.N; i++ {
        Calculate()
    }
}

// After (Go 1.24+)
func BenchmarkNew(b *testing.B) {
    for b.Loop() {
        Calculate()
    }
}
```

#### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "The old pattern still works" | Deprecated. Use modern Go patterns. | **Use b.Loop()** |
| "I'm used to the for loop" | Familiarity ≠ best practice. Adapt. | **Use b.Loop()** |
| "It's just benchmarks" | Standards apply to all test code. | **Use b.Loop()** |
| "We're on Go 1.23" | Upgrade to Go 1.24+ (minimum version requirement). | **Upgrade + use b.Loop()** |

### Environment Variables in Tests (t.Setenv - MANDATORY)

**HARD GATE:** Integration tests that modify environment variables MUST use `t.Setenv()` instead of `os.Setenv()`.

#### Why t.Setenv Is MANDATORY

| Feature | `os.Setenv()` | `t.Setenv()` |
|---------|---------------|--------------|
| Auto-cleanup | ❌ No - leaks to other tests | ✅ Yes - restored after test |
| Test isolation | ❌ Breaks parallel tests | ✅ Safe for parallel tests |
| Subtest scoping | ❌ Affects all subtests | ✅ Scoped to current test/subtest |
| t.Parallel() compatible | ❌ Race conditions | ✅ Safe |

#### Correct Pattern (REQUIRED)

```go
func TestConfig_LoadFromEnv(t *testing.T) {
    // ✅ CORRECT: t.Setenv auto-cleans after test
    t.Setenv("DB_HOST", "localhost")
    t.Setenv("DB_PORT", "5432")
    t.Setenv("DB_NAME", "test_db")

    cfg, err := LoadConfig()
    require.NoError(t, err)
    assert.Equal(t, "localhost", cfg.DBHost)
    assert.Equal(t, "5432", cfg.DBPort)
}

func TestConfig_WithSubtests(t *testing.T) {
    t.Run("production config", func(t *testing.T) {
        // ✅ Scoped to this subtest only
        t.Setenv("ENV", "production")
        t.Setenv("LOG_LEVEL", "info")

        cfg := LoadConfig()
        assert.Equal(t, "production", cfg.Env)
    })

    t.Run("development config", func(t *testing.T) {
        // ✅ Previous subtest's env vars are already cleaned up
        t.Setenv("ENV", "development")
        t.Setenv("LOG_LEVEL", "debug")

        cfg := LoadConfig()
        assert.Equal(t, "development", cfg.Env)
    })
}

func TestConfig_Parallel(t *testing.T) {
    t.Run("test1", func(t *testing.T) {
        t.Parallel()
        t.Setenv("API_KEY", "key1")  // ✅ Safe with t.Parallel()
        // ...
    })

    t.Run("test2", func(t *testing.T) {
        t.Parallel()
        t.Setenv("API_KEY", "key2")  // ✅ Isolated from test1
        // ...
    })
}
```

#### FORBIDDEN Pattern

```go
// ❌ FORBIDDEN: os.Setenv in tests
func TestConfig_LoadFromEnv(t *testing.T) {
    os.Setenv("DB_HOST", "localhost")     // WRONG: leaks to other tests
    os.Setenv("DB_PORT", "5432")          // WRONG: not cleaned up
    defer os.Unsetenv("DB_HOST")          // WRONG: manual cleanup is error-prone
    defer os.Unsetenv("DB_PORT")          // WRONG: forgotten if test panics

    cfg, err := LoadConfig()
    // ...
}

// ❌ FORBIDDEN: os.Setenv with manual cleanup
func TestConfig_Manual(t *testing.T) {
    originalHost := os.Getenv("DB_HOST")
    os.Setenv("DB_HOST", "test-host")
    defer os.Setenv("DB_HOST", originalHost)  // WRONG: verbose, error-prone
    // ...
}
```

#### Detection Command

```bash
# Find os.Setenv in test files (should return 0 matches)
grep -rn "os\.Setenv" --include="*_test.go" ./internal ./pkg ./cmd

# If matches found → Replace with t.Setenv
```

#### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "I use defer os.Unsetenv" | Defer doesn't run if test panics. t.Setenv always cleans up. | **Use t.Setenv** |
| "Tests run sequentially anyway" | Today yes, tomorrow parallel. Write tests correctly from start. | **Use t.Setenv** |
| "It's just one env var" | One var can break other tests. No exceptions. | **Use t.Setenv** |
| "t.Setenv didn't exist before" | It exists since Go 1.17. Use it. | **Use t.Setenv** |
| "I restore the original value" | Verbose, error-prone, unnecessary. t.Setenv handles it. | **Use t.Setenv** |

---

## Logging

**HARD GATE:** All Go services MUST use lib-commons structured logging. Unstructured logging is FORBIDDEN.

### FORBIDDEN Logging Patterns (CRITICAL - Automatic FAIL)

| Pattern | Why FORBIDDEN | Detection Command |
|---------|---------------|-------------------|
| `fmt.Println()` | No structure, no trace correlation, unsearchable | `grep -rn "fmt.Println" --include="*.go"` |
| `fmt.Printf()` | No structure, no trace correlation, unsearchable | `grep -rn "fmt.Printf" --include="*.go"` |
| `log.Println()` | Standard library logger lacks trace correlation | `grep -rn "log.Println" --include="*.go"` |
| `log.Printf()` | Standard library logger lacks trace correlation | `grep -rn "log.Printf" --include="*.go"` |
| `log.Fatal()` | Exits without graceful shutdown, breaks telemetry flush | `grep -rn "log.Fatal" --include="*.go"` |
| `println()` | Built-in, no structure, debugging only | `grep -rn "println(" --include="*.go"` |

**If any of these patterns are found in production code → REVIEW FAILS. no EXCEPTIONS.**

### Pre-Commit Check (MANDATORY)

Add to `.golangci.yml` or run manually before commit:

```bash
# MUST pass with zero matches before commit
grep -rn "fmt.Println\|fmt.Printf\|log.Println\|log.Printf\|log.Fatal\|println(" --include="*.go" ./internal ./cmd
# Expected output: (nothing - no matches)
```

### Using lib-commons Logger (REQUIRED Pattern)

```go
// CORRECT: Recover logger from context
logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

// CORRECT: Log with context correlation
logger.Infof("Processing entity: %s", entityID)
logger.Warnf("Rate limit approaching: %d/%d", current, limit)
logger.Errorf("Failed to save entity: %v", err)
```

### Migration Examples

```go
// ❌ FORBIDDEN: fmt.Println
fmt.Println("Starting server...")

// ✅ REQUIRED: lib-commons logger
logger.Info("Starting server")

// ❌ FORBIDDEN: fmt.Printf  
fmt.Printf("Processing user: %s\n", userID)

// ✅ REQUIRED: lib-commons logger
logger.Infof("Processing user: %s", userID)

// ❌ FORBIDDEN: log.Printf
log.Printf("[ERROR] Failed to connect: %v", err)

// ✅ REQUIRED: lib-commons logger with span error
logger.Errorf("Failed to connect: %v", err)
libOpentelemetry.HandleSpanError(&span, "Connection failed", err)

// ❌ FORBIDDEN: log.Fatal (breaks graceful shutdown)
log.Fatal("Cannot start without config")

// ✅ REQUIRED: panic in bootstrap only (caught by recovery middleware)
panic(fmt.Errorf("cannot start without config: %w", err))
```

### What not to Log (Sensitive Data)

```go
// FORBIDDEN - sensitive data
logger.Info("user login", "password", password)  // never
logger.Info("payment", "card_number", card)      // never
logger.Info("auth", "token", token)              // never
logger.Info("user", "cpf", cpf)                  // never (PII)
```

### golangci-lint Custom Rule (RECOMMENDED)

Add to `.golangci.yml` to automatically fail CI on forbidden patterns:

```yaml
linters-settings:
  forbidigo:
    forbid:
      - p: ^fmt\.Print.*$
        msg: "FORBIDDEN: Use lib-commons logger instead of fmt.Print*"
      - p: ^log\.(Print|Fatal|Panic).*$
        msg: "FORBIDDEN: Use lib-commons logger instead of standard log package"
      - p: ^print$
        msg: "FORBIDDEN: Use lib-commons logger instead of print builtin"
      - p: ^println$
        msg: "FORBIDDEN: Use lib-commons logger instead of println builtin"

linters:
  enable:
    - forbidigo
```

---

## Linting

### Import Ordering (MANDATORY)

**HARD GATE:** All Go files MUST follow the standard import ordering. Unordered imports trigger linter warnings and CodeRabbit violations.

#### Import Order (3 Groups)

```go
import (
    // Group 1: Standard library
    "context"
    "fmt"
    "time"

    // Group 2: Third-party packages
    "github.com/gofiber/fiber/v2"
    "go.uber.org/zap"

    // Group 3: Local/project packages
    libCommons "github.com/LerianStudio/lib-commons/v2/commons"
    libLog "github.com/LerianStudio/lib-commons/v2/commons/log"
    "github.com/your-org/your-service/internal/domain"
)
```

#### Rules

| Rule | Description |
|------|-------------|
| **Group 1 first** | Standard library (`fmt`, `context`, `time`, etc.) |
| **Group 2 second** | Third-party packages (external dependencies) |
| **Group 3 third** | Local packages (your project's internal packages) |
| **Blank line between groups** | Each group separated by one blank line |
| **Alphabetical within group** | Imports sorted alphabetically within each group |
| **lib-commons in Group 3** | lib-commons is a Lerian package, goes in local group |

#### Correct Pattern

```go
// ✅ CORRECT: Proper import ordering
import (
    // Standard library
    "context"
    "errors"
    "fmt"
    "time"

    // Third-party
    "github.com/gofiber/fiber/v2"
    "github.com/google/uuid"
    "go.opentelemetry.io/otel/trace"

    // Local/Lerian packages
    libCommons "github.com/LerianStudio/lib-commons/v2/commons"
    libLog "github.com/LerianStudio/lib-commons/v2/commons/log"
    libOpentelemetry "github.com/LerianStudio/lib-commons/v2/commons/opentelemetry"
    "github.com/your-org/your-service/internal/domain"
    "github.com/your-org/your-service/internal/repository"
)
```

#### FORBIDDEN Patterns

```go
// ❌ FORBIDDEN: Mixed groups without separation
import (
    "context"
    "github.com/gofiber/fiber/v2"
    "fmt"
    "github.com/your-org/your-service/internal/domain"
    "time"
)

// ❌ FORBIDDEN: Wrong order (third-party before stdlib)
import (
    "github.com/gofiber/fiber/v2"
    "context"
    "fmt"
)

// ❌ FORBIDDEN: No blank lines between groups
import (
    "context"
    "fmt"
    "github.com/gofiber/fiber/v2"
    "github.com/your-org/your-service/internal/domain"
)
```

#### Automatic Fixing

```bash
# Fix import ordering automatically
goimports -w .

# Or use golangci-lint with goimports
golangci-lint run --fix ./...
```

#### Agent Execution (MANDATORY)

**HARD GATE:** After generating or modifying Go files, agents MUST run `goimports` to ensure correct import ordering.

```bash
# Agent MUST execute after code generation:
goimports -w ./internal ./cmd ./pkg
```

| When | Agent Action |
|------|--------------|
| After creating new file | Run `goimports -w {file}` |
| After modifying imports | Run `goimports -w {file}` |
| Before completing task | Run `goimports -w ./internal ./cmd ./pkg` |

**Why agents must run this:**
- Generated code may have imports in wrong order
- IDE auto-formatting not available in agent context
- Prevents linter failures in CI/CD
- Ensures clean code review (no import noise)

#### golangci-lint Configuration

```yaml
# .golangci.yml
linters:
  enable:
    - goimports
    - gci

linters-settings:
  goimports:
    local-prefixes: github.com/LerianStudio,github.com/your-org

  gci:
    sections:
      - standard                          # Standard library
      - default                           # Third-party
      - prefix(github.com/LerianStudio)   # Lerian packages
      - prefix(github.com/your-org)       # Project packages
    skip-generated: true
```

#### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "goimports will fix it" | CI may not have --fix. Code review sees the mess. | **Fix before commit** |
| "Import order doesn't affect runtime" | Readability and maintainability matter. | **Follow the standard** |
| "I'll fix it later" | Later = never. Fix now. | **Run goimports before commit** |
| "My IDE doesn't auto-sort" | Configure your IDE or run goimports manually. | **Set up tooling** |

---

### Magic Numbers (FORBIDDEN)

**HARD GATE:** Code with literal numeric values (magic numbers) is FORBIDDEN. All numbers MUST be declared as named constants.

#### Why Magic Numbers Are FORBIDDEN

| Problem | Impact |
|---------|--------|
| **No semantic meaning** | `if attempts > 3` - What does 3 mean? Max retries? |
| **Maintenance nightmare** | Same number in 10 places → change requires finding all |
| **No IDE support** | Cannot "Find References" on a literal `3` |
| **Silent bugs** | Two unrelated `3`s changed together by accident |

#### Allowed Exceptions

| Value | Allowed Where | Reason |
|-------|---------------|--------|
| `0` | Zero initialization | Universal zero value |
| `1` | Increment/decrement | Mathematical identity |
| `-1` | Not found indicators | Common convention |
| Test data | `_test.go` files only | Test cases use arbitrary values |

#### Anti-Patterns (FORBIDDEN)

```go
// ❌ FORBIDDEN: Magic numbers without context
func ProcessOrder(order Order) error {
    if order.Total > 10000 {          // What is 10000?
        return ErrAmountTooHigh
    }
    if len(order.Items) > 50 {        // Why 50?
        return ErrTooManyItems
    }
    time.Sleep(5 * time.Second)       // Why 5 seconds?
    return nil
}

// ❌ FORBIDDEN: Magic numbers in conditions
if retries > 3 {                      // What does 3 represent?
    return ErrMaxRetriesExceeded
}

// ❌ FORBIDDEN: Magic numbers in slices
data := make([]byte, 4096)            // Why 4096?
```

#### Correct Patterns (REQUIRED)

```go
// ✅ CORRECT: Named constants with semantic meaning
const (
    MaxOrderAmount     = 10000        // BRL - business rule limit
    MaxItemsPerOrder   = 50           // Performance constraint
    RetryDelaySeconds  = 5            // Backoff between retries
    MaxRetryAttempts   = 3            // Circuit breaker threshold
    DefaultBufferSize  = 4096         // 4KB buffer for file I/O
)

func ProcessOrder(order Order) error {
    if order.Total > MaxOrderAmount {
        return ErrAmountTooHigh
    }
    if len(order.Items) > MaxItemsPerOrder {
        return ErrTooManyItems
    }
    time.Sleep(RetryDelaySeconds * time.Second)
    return nil
}

// ✅ CORRECT: Constants in conditions
if retries > MaxRetryAttempts {
    return ErrMaxRetriesExceeded
}

// ✅ CORRECT: Named buffer size
data := make([]byte, DefaultBufferSize)
```

#### Constant Naming Convention

| Type | Prefix | Example |
|------|--------|---------|
| Maximum limits | `Max` | `MaxRetries`, `MaxConnections` |
| Minimum limits | `Min` | `MinPasswordLength` |
| Default values | `Default` | `DefaultTimeout`, `DefaultPageSize` |
| Size/capacity | Size/Capacity | `BufferSize`, `PoolCapacity` |
| Duration | `*Duration` or `*Seconds` | `TimeoutDuration`, `RetryDelaySeconds` |

#### Detection

```bash
# Find potential magic numbers (review each)
grep -rn "[^a-zA-Z0-9_][0-9]\{2,\}[^a-zA-Z0-9_]" --include="*.go" ./internal ./pkg | grep -v "_test.go"

# golangci-lint with mnd linter (automated)
golangci-lint run --enable=mnd ./...
```

---

### Post-Implementation Linting (MANDATORY)

**HARD GATE:** After ANY code generation, modification, or refactoring, agents MUST run `golangci-lint` to catch violations before completing the task.

#### When to Run

| Trigger | Command | Why |
|---------|---------|-----|
| After creating new files | `golangci-lint run {path}` | Catch violations immediately |
| After modifying code | `golangci-lint run {path}` | Validate changes |
| After refactoring | `golangci-lint run ./...` | Full project scan |
| Before completing task | `golangci-lint run ./...` | Final validation |
| Before commit | `golangci-lint run ./...` | Pre-commit check |

#### Agent Execution Pattern

```bash
# 1. After code generation/modification
goimports -w ./internal ./cmd ./pkg

# 2. Run linter
golangci-lint run ./internal ./cmd ./pkg

# 3. If violations found → Fix them
# 4. Re-run until clean
golangci-lint run ./internal ./cmd ./pkg  # Should output: no issues found
```

#### Benefits of Running During Development

| Benefit | Explanation |
|---------|-------------|
| **Early detection** | Find issues immediately, not in CI |
| **Faster iteration** | Fix while context is fresh |
| **Clean commits** | No linter noise in code review |
| **CI/CD success** | Passes automated checks first time |

#### Example Workflow

```bash
# Agent generates UserService.go
# Step 1: Fix imports
goimports -w internal/service/user_service.go

# Step 2: Run linter
golangci-lint run internal/service/user_service.go
# Output: internal/service/user_service.go:15:2: var unusedVar is unused (unused)

# Step 3: Fix violation
# (Agent removes unusedVar)

# Step 4: Re-run linter
golangci-lint run internal/service/user_service.go
# Output: (no issues found)

# ✅ Task complete - code is clean
```

#### FORBIDDEN Patterns

```go
// ❌ FORBIDDEN: Completing task with linter violations
Agent: "I've generated UserService.go. Task complete."
// WRONG: Didn't run golangci-lint

// ❌ FORBIDDEN: Ignoring linter output
golangci-lint run ./...
# Output: 15 issues found
Agent: "Minor linter issues, skipping."
// WRONG: Must fix ALL issues

// ❌ FORBIDDEN: Running linter but not fixing
golangci-lint run ./...
# Output: magic number detected
Agent: "Linter shows magic number, but I'll leave it."
// WRONG: Must fix before completing
```

#### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "CI will catch it" | CI is too late. Fix during development. | **Run linter now** |
| "It's just a warning" | Warnings become errors. Fix them. | **Fix all issues** |
| "I'll fix in next PR" | Next PR = never. Fix now. | **Fix before completing** |
| "Linter is too strict" | Standards exist for a reason. Follow them. | **Fix violations** |
| "It's a false positive" | Rare. Investigate before assuming. | **Fix or use //nolint with reason** |

---

### golangci-lint Configuration

```yaml
# .golangci.yml
linters:
  enable:
    - errcheck      # Check error handling
    - govet         # Go vet
    - staticcheck   # Static analysis
    - gosimple      # Simplify code
    - ineffassign   # Unused assignments
    - unused        # Unused code
    - gofmt         # Formatting
    - goimports     # Import ordering
    - misspell      # Spelling
    - goconst       # Repeated strings
    - gosec         # Security issues
    - nilerr        # Return nil with non-nil error
    - mnd           # Magic number detector

linters-settings:
  mnd:
    # Checks to enable (default: argument,case,condition,operation,return,assign)
    checks:
      - argument
      - case
      - condition
      - operation
      - return
      - assign
    # Ignored numbers (0, 1 are always allowed)
    ignored-numbers:
      - '0'
      - '1'
      - '-1'
    # Ignored functions (regex patterns)
    ignored-functions:
      - '^math\.'
      - '^http\.Status'
      - '^strings\.(SplitN|SplitAfterN)'
    # Ignored files
    ignored-files:
      - '_test\.go$'
```

### Format Commands

```bash
# Format code
gofmt -w .
goimports -w .

# Run linter
golangci-lint run ./...

# Run only magic number check
golangci-lint run --enable=mnd --disable-all ./...
```

---

