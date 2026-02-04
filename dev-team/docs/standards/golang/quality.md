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
```

### Format Commands

```bash
# Format code
gofmt -w .
goimports -w .

# Run linter
golangci-lint run ./...
```

---

