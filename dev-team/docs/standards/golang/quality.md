# Go Standards - Quality

> **Module:** quality.md | **Sections:** 4 | **Parent:** [index.md](index.md)

This module covers logging, linting, configuration validation, and container security standards.

> **Note:** Testing standards have been moved to dedicated modules:
> - [testing-unit.md](testing-unit.md) - Unit testing patterns (Gate 3)
> - [testing-fuzz.md](testing-fuzz.md) - Fuzz testing patterns (Gate 4)
> - [testing-property.md](testing-property.md) - Property-based testing patterns (Gate 5)
> - [testing-integration.md](testing-integration.md) - Integration testing patterns (Gate 6)
> - [testing-chaos.md](testing-chaos.md) - Chaos testing patterns (Gate 7)
> - [testing-benchmark.md](testing-benchmark.md) - Benchmark testing patterns (optional)

---

## Table of Contents

| # | [Section Name](#anchor-link) | Description |
|---|------------------------------|-------------|
| 1 | [Logging](#logging) | Structured logging with lib-commons |
| 2 | [Linting](#linting) | Import ordering, magic numbers, .golangci.yml requirement |
| 3 | [Production Config Validation](#production-config-validation-mandatory) | Startup validation and fail-fast |
| 4 | [Container Security](#container-security-conditional) | Non-root user, image pinning |

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

**HARD GATE:** MUST run `goimports` after generating or modifying Go files to ensure correct import ordering.

```bash
# Agent MUST execute after code generation:
goimports -w ./internal ./cmd ./pkg
```

| When | Agent Action |
|------|--------------|
| After creating new file | Run `goimports -w {file}` |
| After modifying imports | Run `goimports -w {file}` |
| Before completing task | Run `goimports -w ./internal ./cmd ./pkg` |

---

### Magic Numbers (FORBIDDEN)

**HARD GATE:** Code with literal numeric values (magic numbers) is FORBIDDEN. All numbers MUST be declared as named constants.

#### Why Magic Numbers Are FORBIDDEN

| Problem | Impact |
|---------|--------|
| **No semantic meaning** | `if attempts > 3` - What does 3 mean? Max retries? |
| **Maintenance nightmare** | Same number in 10 places → change requires finding all |
| **No IDE support** | Cannot "Find References" on a literal `3` |
| **Silent bugs** | Two unrelated `3`s changed together accidentally |

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
```

#### Constant Naming Convention

| Type | Prefix | Example |
|------|--------|---------|
| Maximum limits | `Max` | `MaxRetries`, `MaxConnections` |
| Minimum limits | `Min` | `MinPasswordLength` |
| Default values | `Default` | `DefaultTimeout`, `DefaultPageSize` |
| Size/capacity | Size/Capacity | `BufferSize`, `PoolCapacity` |
| Duration | `*Duration` or `*Seconds` | `TimeoutDuration`, `RetryDelaySeconds` |

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

---

### .golangci.yml Requirement (MANDATORY)

Projects without `.golangci.yml` have inconsistent linting across environments, leading to CI failures and code review noise.

**⛔ HARD GATE:** Every Go project MUST have a `.golangci.yml` file in the repository root. Missing this file is a BLOCKER for code review.

#### Minimum Required Linters (MANDATORY)

Every `.golangci.yml` MUST enable these linters:

| Linter | Purpose | Category |
|--------|---------|----------|
| `gofmt` | Code formatting | Style |
| `goimports` | Import organization | Style |
| `govet` | Go vet analysis | Correctness |
| `staticcheck` | Static analysis | Correctness |
| `errcheck` | Error handling verification | Correctness |
| `gosec` | Security vulnerability detection | Security |
| `mnd` | Magic number detection | Quality |
| `unused` | Unused code detection | Quality |
| `ineffassign` | Unused assignment detection | Quality |

#### Configuration Template

```yaml
# .golangci.yml - Minimum required configuration
run:
  timeout: 5m
  go: '1.24'

linters:
  disable-all: true
  enable:
    # MANDATORY linters (MUST be enabled)
    - gofmt         # Code formatting
    - goimports     # Import organization
    - govet         # Go vet analysis
    - staticcheck   # Static analysis
    - errcheck      # Error handling verification
    - gosec         # Security vulnerability detection
    - mnd           # Magic number detection
    - unused        # Unused code detection
    - ineffassign   # Unused assignment detection
    # Recommended additional linters
    - gosimple      # Simplify code
    - misspell      # Spelling
    - goconst       # Repeated strings
    - nilerr        # Return nil with non-nil error
    - forbidigo     # Forbidden patterns

linters-settings:
  goimports:
    local-prefixes: github.com/LerianStudio

  mnd:
    checks:
      - argument
      - case
      - condition
      - operation
      - return
      - assign
    ignored-numbers:
      - '0'
      - '1'
      - '-1'
    ignored-functions:
      - '^math\.'
      - '^http\.Status'
      - '^strings\.(SplitN|SplitAfterN)'
    ignored-files:
      - '_test\.go$'

  forbidigo:
    forbid:
      - p: ^fmt\.Print.*$
        msg: "FORBIDDEN: Use lib-commons logger"
      - p: ^log\.(Print|Fatal|Panic).*$
        msg: "FORBIDDEN: Use lib-commons logger"
```

---

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

## Production Config Validation (MANDATORY)

Services that start with invalid or missing configuration cause runtime failures instead of fail-fast at startup.

**⛔ HARD GATE:** All services MUST validate configuration at startup and fail fast by returning an error if invalid. Silent failures and panic are FORBIDDEN.

### Why Startup Validation Is MANDATORY

| Issue | Impact Without Validation |
|-------|---------------------------|
| Missing required field | Service starts but fails on first request |
| Invalid format | Silent misbehavior (wrong DB, wrong endpoint) |
| Wrong environment | Production config in dev, or vice versa |
| Connection string typo | Service starts, fails on first DB call |

### Validation Patterns (REQUIRED)

```go
// internal/bootstrap/config.go

type Config struct {
    // Required fields - MUST have validation
    ServerAddress string `env:"SERVER_ADDRESS"`
    DBHost        string `env:"DB_HOST"`
    DBName        string `env:"DB_NAME"`
    DBUser        string `env:"DB_USER"`
    DBPassword    string `env:"DB_PASSWORD"`

    // Optional with defaults
    DBPort        string `env:"DB_PORT" default:"5432"`
    LogLevel      string `env:"LOG_LEVEL" default:"info"`
    MaxPoolSize   int    `env:"DB_MAX_POOL_SIZE" default:"50"`
}

// Validate checks all required fields and returns a detailed error
func (c *Config) Validate() error {
    var errs []string

    // Required field validation
    if c.ServerAddress == "" {
        errs = append(errs, "SERVER_ADDRESS is required")
    }
    if c.DBHost == "" {
        errs = append(errs, "DB_HOST is required")
    }
    if c.DBName == "" {
        errs = append(errs, "DB_NAME is required")
    }
    if c.DBUser == "" {
        errs = append(errs, "DB_USER is required")
    }
    if c.DBPassword == "" {
        errs = append(errs, "DB_PASSWORD is required")
    }

    // Format validation
    if c.MaxPoolSize < 1 || c.MaxPoolSize > 500 {
        errs = append(errs, "DB_MAX_POOL_SIZE must be between 1 and 500")
    }

    validLogLevels := map[string]bool{"debug": true, "info": true, "warn": true, "error": true}
    if !validLogLevels[c.LogLevel] {
        errs = append(errs, "LOG_LEVEL must be one of: debug, info, warn, error")
    }

    if len(errs) > 0 {
        return fmt.Errorf("configuration validation failed:\n- %s", strings.Join(errs, "\n- "))
    }

    return nil
}

// InitServers MUST validate config and return an error on failure (caller logs and exits non-zero)
func InitServers() (*Service, error) {
    cfg := &Config{}
    if err := libCommons.SetConfigFromEnvVars(cfg); err != nil {
        return nil, fmt.Errorf("failed to load config: %w", err)
    }

    // MANDATORY: Validate before any initialization
    if err := cfg.Validate(); err != nil {
        return nil, err
    }

    // Continue with initialization only after validation passes
    logger := libZap.InitializeLogger()
    logger.Info("Configuration validated successfully")

    // ... rest of initialization
    return &Service{...}, nil
}
```

**Caller (e.g. main) MUST log and exit non-zero on error:**

```go
// cmd/server/main.go
func main() {
    logger := libZap.InitializeLogger()
    svc, err := InitServers()
    if err != nil {
        logger.Errorf("startup failed: %v", err)
        os.Exit(1)
    }
    // run svc...
}
```

### FORBIDDEN Patterns

```go
// ❌ FORBIDDEN: No validation at startup
func InitServers() *Service {
    cfg := &Config{}
    libCommons.SetConfigFromEnvVars(cfg)
    // WRONG: No validation - silent failures later
    return &Service{cfg: cfg}
}

// ❌ FORBIDDEN: Validation that returns nil on invalid config (silent failure)
func (c *Config) Validate() error {
    if c.DBHost == "" {
        log.Printf("Warning: DB_HOST not set")  // WRONG: Must return error
        return nil  // WRONG: Silent failure
    }
    return nil
}
```

---

## Container Security (⚠️ CONDITIONAL)

**⛔ CONDITIONAL:** This section applies ONLY if the service has a Dockerfile. If no Dockerfile exists, mark this section as N/A.

**Detection Question:**

```bash
# Check if Dockerfile exists
ls -la Dockerfile

# If file exists: Apply this section
# If file does not exist: Mark N/A
```

Containers running as root and using untagged images (`latest`) cause security vulnerabilities and deployment inconsistencies.

### Non-Root User (MANDATORY if Dockerfile exists)

**⛔ HARD GATE:** Containers MUST NOT run as root. The `USER` directive is REQUIRED in all Dockerfiles.

#### Why Non-Root Is Required

| Risk | Running as Root | Running as Non-Root |
|------|-----------------|---------------------|
| Container escape | Full host access | Limited access |
| File system access | Can write anywhere | Only permitted paths |
| Kubernetes policy | PSP/PSA violations | Compliant |
| Vulnerability exploitation | Elevated privileges | Contained damage |

#### Required Pattern

```dockerfile
# ✅ CORRECT: Multi-stage build with non-root user
FROM golang:1.24-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/server ./cmd/server

FROM alpine:3.19.1
# Security: Create non-root user
RUN addgroup -g 1000 appgroup && \
    adduser -u 1000 -G appgroup -D appuser

WORKDIR /app
COPY --from=builder /app/server .

# Security: Switch to non-root user
USER appuser:appgroup

EXPOSE 8080
CMD ["./server"]
```

#### FORBIDDEN Pattern

```dockerfile
# ❌ FORBIDDEN: No USER directive (runs as root)
FROM golang:1.24-alpine
WORKDIR /app
COPY . .
RUN go build -o server ./cmd/server
EXPOSE 8080
CMD ["./server"]

# ❌ FORBIDDEN: USER root
FROM alpine:3.19
USER root
CMD ["./server"]
```

### Image Pinning (MANDATORY)

**⛔ HARD GATE:** All base images MUST use specific version tags. The `:latest` tag is FORBIDDEN.

| Tag Type | Example | Status |
|----------|---------|--------|
| Exact version | `golang:1.24.0-alpine3.19` | ✅ REQUIRED |
| Minor version | `golang:1.24-alpine` | ⚠️ Acceptable |
| Latest | `golang:latest` | ❌ FORBIDDEN |
| None (implicit latest) | `FROM golang` | ❌ FORBIDDEN |

#### Why Pinning Is Required

| Problem with :latest | Impact |
|---------------------|--------|
| Non-reproducible builds | Works today, breaks tomorrow |
| Security scan bypass | Different image in CI vs prod |
| Debugging nightmare | "It worked on my machine" |
| CVE tracking impossible | Which version has the vulnerability? |

#### Detection Commands

```bash
# Find non-root user in Dockerfile
grep -n "^USER" Dockerfile

# Expected: USER directive exists and is NOT root

# Find image tags
grep -n "^FROM" Dockerfile

# Expected: All FROM statements have explicit version tags (not :latest)

# Check for :latest tag
grep -n "FROM.*:latest\|FROM [a-z]*$" Dockerfile

# Expected: 0 matches
```

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "We trust our images" | Trust but verify. Least privilege always. | **Add USER directive** |
| ":latest is convenient" | Convenience causes incidents. Pin versions. | **Use specific tags** |
| "Kubernetes securityContext handles it" | Defense in depth. Image should be secure too. | **Add USER in Dockerfile** |
| "We rebuild often" | Rebuild with same vulnerability. Pin to known-good. | **Pin to specific version** |
| "It's just internal" | Internal ≠ exempt from security. | **Follow all security patterns** |

---
