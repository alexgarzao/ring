# Go Standards - Domain Patterns

> **Module:** domain.md | **Sections:** §9-12 | **Parent:** [index.md](index.md)

This module covers data transformation, error handling, and function design.

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [Data Transformation: ToEntity/FromEntity](#data-transformation-toentityfromentity-mandatory) | Database model to domain entity conversion |
| 2 | [Error Codes Convention](#error-codes-convention-mandatory) | Service-prefixed error codes |
| 3 | [Error Handling](#error-handling) | Error wrapping and checking rules |
| 4 | [Exit/Fatal Location Rules](#exitfatal-location-rules-mandatory) | Where exit/fatal/panic is allowed |
| 5 | [Function Design](#function-design-mandatory) | Single responsibility principle |

---

## Data Transformation: ToEntity/FromEntity (MANDATORY)

All database models **MUST** implement transformation methods to/from domain entities.

### Pattern

```go
// internal/adapters/postgres/user/user.postgresql.go

// UserPostgreSQLModel is the database representation
type UserPostgreSQLModel struct {
    ID        string         `db:"id"`
    Email     string         `db:"email"`
    Name      string         `db:"name"`
    Status    string         `db:"status"`
    CreatedAt time.Time      `db:"created_at"`
    UpdatedAt time.Time      `db:"updated_at"`
    DeletedAt sql.NullTime   `db:"deleted_at"`
}

// ToEntity converts database model to domain entity
func (m *UserPostgreSQLModel) ToEntity() *domain.User {
    var deletedAt *time.Time
    if m.DeletedAt.Valid {
        deletedAt = &m.DeletedAt.Time
    }

    return &domain.User{
        ID:        domain.UserID(m.ID),
        Email:     domain.Email(m.Email),
        Name:      m.Name,
        Status:    domain.UserStatus(m.Status),
        CreatedAt: m.CreatedAt,
        UpdatedAt: m.UpdatedAt,
        DeletedAt: deletedAt,
    }
}

// FromEntity converts domain entity to database model
func (m *UserPostgreSQLModel) FromEntity(u *domain.User) {
    m.ID = string(u.ID)
    m.Email = string(u.Email)
    m.Name = u.Name
    m.Status = string(u.Status)
    m.CreatedAt = u.CreatedAt
    m.UpdatedAt = u.UpdatedAt
    if u.DeletedAt != nil {
        m.DeletedAt = sql.NullTime{Time: *u.DeletedAt, Valid: true}
    }
}
```

### Why This Matters

- **Layer isolation**: Domain doesn't know about database concerns
- **Testability**: Domain entities can be tested without database
- **Flexibility**: Database schema can change without affecting domain
- **Type safety**: Explicit conversions prevent accidental mixing

---

## Error Codes Convention (MANDATORY)

Each service **MUST** define error codes with a service-specific prefix.

### Service Prefixes

| Service | Prefix | Example |
|---------|--------|---------|
| Lerian | LRN | LRN-0001 |
| Plugin-Fees | FEE | FEE-0001 |
| Plugin-Auth | AUT | AUT-0001 |
| Platform | PLT | PLT-0001 |

### Error Code Structure

```go
// pkg/constant/errors.go
package constant

const (
    ErrCodeInvalidInput     = "PLT-0001"
    ErrCodeNotFound         = "PLT-0002"
    ErrCodeUnauthorized     = "PLT-0003"
    ErrCodeForbidden        = "PLT-0004"
    ErrCodeConflict         = "PLT-0005"
    ErrCodeInternalError    = "PLT-0006"
    ErrCodeValidationFailed = "PLT-0007"
)

// Error definitions with messages
var (
    ErrInvalidInput = &BusinessError{
        Code:    ErrCodeInvalidInput,
        Message: "Invalid input provided",
    }
    ErrNotFound = &BusinessError{
        Code:    ErrCodeNotFound,
        Message: "Resource not found",
    }
)
```

### Business Error Type

```go
// pkg/errors.go
type BusinessError struct {
    Code    string `json:"code"`
    Message string `json:"message"`
    Details any    `json:"details,omitempty"`
}

func (e *BusinessError) Error() string {
    return fmt.Sprintf("[%s] %s", e.Code, e.Message)
}

func ValidateBusinessError(err *BusinessError, entityType string, args ...any) error {
    // Format error with entity context
    return &BusinessError{
        Code:    err.Code,
        Message: fmt.Sprintf(err.Message, args...),
        Details: map[string]string{"entity": entityType},
    }
}
```

---

## Error Handling

### Sentinel Errors (MANDATORY)

**HARD GATE:** All domain/business errors MUST be defined as sentinel errors (package-level variables). Creating errors inline with `errors.New()` or `fmt.Errorf()` for known error conditions is FORBIDDEN.

#### Why Sentinel Errors Are MANDATORY

| Benefit | Explanation |
|---------|-------------|
| **Comparability** | Callers can use `errors.Is(err, ErrNotFound)` for precise handling |
| **Documentation** | All possible errors are visible in one place |
| **Type safety** | IDE autocomplete, refactoring support |
| **Testing** | Tests can assert exact error types |
| **API contracts** | Errors are part of the public API |

#### Correct Pattern (REQUIRED)

```go
// pkg/errors/errors.go - Define all sentinel errors
package errors

import "errors"

// Domain errors - sentinel values
var (
    ErrNotFound          = errors.New("resource not found")
    ErrAlreadyExists     = errors.New("resource already exists")
    ErrInvalidInput      = errors.New("invalid input")
    ErrUnauthorized      = errors.New("unauthorized")
    ErrForbidden         = errors.New("forbidden")
    ErrInsufficientFunds = errors.New("insufficient funds")
    ErrExpired           = errors.New("resource expired")
)

// Service-specific errors
var (
    ErrUserNotFound      = errors.New("user not found")
    ErrUserAlreadyExists = errors.New("user already exists")
    ErrInvalidEmail      = errors.New("invalid email format")
    ErrEmailTaken        = errors.New("email already taken")
)
```

```go
// internal/service/user.go - Use sentinel errors
package service

import (
    "errors"
    "fmt"

    pkgErrors "github.com/your-org/your-service/pkg/errors"
)

func (s *UserService) GetUser(ctx context.Context, id string) (*User, error) {
    user, err := s.repo.FindByID(ctx, id)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, pkgErrors.ErrUserNotFound  // ✅ Return sentinel
        }
        return nil, fmt.Errorf("failed to get user: %w", err)  // ✅ Wrap unknown errors
    }
    return user, nil
}
```

```go
// Caller can check specific errors
user, err := userService.GetUser(ctx, id)
if err != nil {
    if errors.Is(err, pkgErrors.ErrUserNotFound) {
        return c.Status(404).JSON(fiber.Map{"error": "user not found"})
    }
    return c.Status(500).JSON(fiber.Map{"error": "internal error"})
}
```

#### FORBIDDEN Patterns

```go
// ❌ FORBIDDEN: Inline error creation for known conditions
func (s *UserService) GetUser(ctx context.Context, id string) (*User, error) {
    user, err := s.repo.FindByID(ctx, id)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, errors.New("user not found")  // WRONG: cannot compare with errors.Is
        }
        return nil, err
    }
    return user, nil
}

// ❌ FORBIDDEN: fmt.Errorf for known error types
func (s *UserService) CreateUser(ctx context.Context, input CreateUserInput) (*User, error) {
    existing, _ := s.repo.FindByEmail(ctx, input.Email)
    if existing != nil {
        return nil, fmt.Errorf("email %s already taken", input.Email)  // WRONG: not a sentinel
    }
    // ...
}

// ❌ FORBIDDEN: String comparison for errors
if err.Error() == "user not found" {  // WRONG: brittle, breaks on message change
    // handle
}
```

#### When fmt.Errorf IS Allowed

```go
// ✅ ALLOWED: Wrapping errors with context (unknown/external errors)
if err != nil {
    return fmt.Errorf("failed to connect to database: %w", err)
}

// ✅ ALLOWED: Adding context to sentinel errors
return fmt.Errorf("user %s: %w", userID, pkgErrors.ErrNotFound)

// ✅ ALLOWED: Truly unexpected errors with dynamic context
return fmt.Errorf("unexpected response from API: status=%d, body=%s", status, body)
```

#### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "The error message is descriptive enough" | Descriptive ≠ comparable. Callers cannot use `errors.Is()`. | **Define sentinel error** |
| "No one needs to check this specific error" | You don't know future callers. Make errors checkable. | **Define sentinel error** |
| "It's just a validation error" | Validation errors are domain errors. Define them. | **Define sentinel error** |
| "I'm wrapping with context anyway" | Wrap sentinels: `fmt.Errorf("context: %w", ErrNotFound)` | **Define sentinel, then wrap** |
| "Too many error variables" | Explicit > implicit. All errors documented in one place. | **Define all sentinels** |

### Error Wrapping Rules

```go
// always check errors
if err != nil {
    return fmt.Errorf("context: %w", err)
}

// always wrap errors with context
if err != nil {
    return fmt.Errorf("failed to create user %s: %w", userID, err)
}

// Check specific errors with errors.Is
if errors.Is(err, ErrUserNotFound) {
    return nil, status.Error(codes.NotFound, "user not found")
}
```

### Forbidden

```go
// never use panic for business logic
panic(err) // FORBIDDEN

// never ignore errors
result, _ := doSomething() // FORBIDDEN

// never return nil error without checking
return nil, nil // SUSPICIOUS - check if error is possible
```

---

## Exit/Fatal Location Rules (MANDATORY)

**HARD GATE:** Internal functions MUST return errors. They CANNOT terminate the program.

### Where Exit/Fatal Is Allowed

| Location | `log.Fatal` / `os.Exit` | `panic` | `return error` |
|----------|-------------------------|---------|----------------|
| `main()` | ✅ Acceptable | ✅ Last resort | N/A |
| Bootstrap/init | ❌ FORBIDDEN | ⚠️ Only unrecoverable | ✅ Preferred |
| Internal functions | ❌ FORBIDDEN | ❌ FORBIDDEN | ✅ MANDATORY |
| Validation functions | ❌ FORBIDDEN | ❌ FORBIDDEN | ✅ MANDATORY |
| Handlers/Services | ❌ FORBIDDEN | ❌ FORBIDDEN | ✅ MANDATORY |
| Repository/Adapters | ❌ FORBIDDEN | ❌ FORBIDDEN | ✅ MANDATORY |

### Why This Matters

- `log.Fatal()` and `os.Exit()` terminate immediately without cleanup
- Callers cannot handle the error or provide user feedback
- Telemetry/tracing data is lost (no flush)
- Graceful shutdown hooks don't run
- Tests cannot capture the error condition

### Anti-Patterns (FORBIDDEN)

```go
// ❌ FORBIDDEN: fatal inside validation function
func validateJSON(data []byte) {
    if !json.Valid(data) {
        log.Fatal("invalid JSON")  // WRONG: kills the process
    }
}

// ❌ FORBIDDEN: panic inside internal function
func parseConfig(path string) Config {
    data, err := os.ReadFile(path)
    if err != nil {
        panic(err)  // WRONG: caller cannot recover
    }
    // ...
}

// ❌ FORBIDDEN: os.Exit inside service layer
func (s *UserService) CreateUser(ctx context.Context, input CreateUserInput) {
    if input.Email == "" {
        os.Exit(1)  // WRONG: catastrophic for a validation error
    }
}
```

### Correct Patterns (REQUIRED)

```go
// ✅ CORRECT: validation returns error
func validateJSON(data []byte) error {
    if !json.Valid(data) {
        return errors.New("invalid JSON format")
    }
    return nil
}

// ✅ CORRECT: internal function returns error
func parseConfig(path string) (Config, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return Config{}, fmt.Errorf("failed to read config %s: %w", path, err)
    }
    // ...
    return config, nil
}

// ✅ CORRECT: main() handles fatal conditions with log.Fatalf (NOT panic)
func main() {
    config, err := parseConfig("config.yaml")
    if err != nil {
        log.Fatalf("Cannot start: %v", err)  // log.Fatalf is OK - logs and exits cleanly
    }
    // ...
}
```

### panic() Detection Checklist (MANDATORY)

**⛔ HARD GATE:** Zero panic() calls allowed ANYWHERE in the codebase (except test files). This includes `cmd/`, `internal/`, and `pkg/` directories.

| panic() Type | Where Found | Verdict | Action |
|--------------|-------------|---------|--------|
| Direct `panic(err)` | Any directory | ❌ FORBIDDEN | Convert to `return err` or `log.Fatalf()` |
| Direct `panic("message")` | Any directory | ❌ FORBIDDEN | Convert to `return errors.New()` or `log.Fatalf()` |
| `panic(fmt.Sprintf(...))` | Any directory | ❌ FORBIDDEN | Convert to `return fmt.Errorf()` or `log.Fatalf()` |
| Must-functions `panicOnErr()` | Any directory | ❌ FORBIDDEN | Remove helper, propagate errors |
| `panic()` in main() | cmd/*/main.go | ❌ FORBIDDEN | Use `log.Fatalf()` instead |

**Detection Commands:**

```bash
# MANDATORY: Run before every PR - check ALL directories
grep -rn "panic(" cmd/ internal/ pkg/ --include="*.go" | grep -v "_test.go"

# Find must-functions (panic wrappers)
grep -rn "func must\|panicOnErr\|panicIf" . --include="*.go" | grep -v "_test.go" | grep -v vendor/

# Expected result: 0 matches
# If any match found: STOP. Fix before proceeding.
```

**✅ CORRECT Alternative:**

```go
// ❌ FORBIDDEN: must-function pattern
func mustParseURL(raw string) *url.URL {
    u, err := url.Parse(raw)
    if err != nil {
        panic(err)  // WRONG
    }
    return u
}

// ✅ CORRECT: Return error
func parseURL(raw string) (*url.URL, error) {
    u, err := url.Parse(raw)
    if err != nil {
        return nil, fmt.Errorf("invalid URL %q: %w", raw, err)
    }
    return u, nil
}
```

### log.Fatal() Location Rules (MANDATORY)

**⛔ HARD GATE:** `log.Fatal()` and `os.Exit()` are ONLY allowed in `main()` or immediate bootstrap failure.

| Call Type | Location | Verdict | Why |
|-----------|----------|---------|-----|
| `log.Fatal()` | `main.go:main()` | ✅ Allowed | Process startup failure |
| `log.Fatal()` | `cmd/*/main.go` | ✅ Allowed | CLI entry point |
| `log.Fatal()` | `internal/service/*.go` | ❌ FORBIDDEN | Service cannot decide process fate |
| `log.Fatal()` | `internal/bootstrap/*.go` | ⚠️ Review | Only for truly unrecoverable (missing DB) |
| `os.Exit()` | Anywhere except main() | ❌ FORBIDDEN | Prevents cleanup, loses telemetry |

**Detection Commands:**

```bash
# MANDATORY: Run before every PR
grep -rn "log\.Fatal" internal/ pkg/ --include="*.go" | grep -v "_test.go"

# Check os.Exit usage
grep -rn "os\.Exit" internal/ pkg/ --include="*.go" | grep -v "_test.go"

# Expected result: 0 matches in internal/pkg
# If any match found: STOP. Fix before proceeding.
```

**✅ CORRECT Alternative:**

```go
// ❌ FORBIDDEN: log.Fatal in internal function
func connectDB(dsn string) *sql.DB {
    db, err := sql.Open("postgres", dsn)
    if err != nil {
        log.Fatal(err)  // WRONG: caller cannot handle
    }
    return db
}

// ✅ CORRECT: Return error to caller
func connectDB(dsn string) (*sql.DB, error) {
    db, err := sql.Open("postgres", dsn)
    if err != nil {
        return nil, fmt.Errorf("failed to connect to database: %w", err)
    }
    if err := db.Ping(); err != nil {
        return nil, fmt.Errorf("database ping failed: %w", err)
    }
    return db, nil
}

// ✅ CORRECT: main() decides process fate
func main() {
    db, err := connectDB(os.Getenv("DATABASE_URL"))
    if err != nil {
        log.Fatalf("Cannot start: %v", err)  // OK in main()
    }
    defer db.Close()
    // ...
}
```

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "This error is truly fatal" | You don't decide. Let main() decide. | **Return error, let caller handle** |
| "panic() is for programmer errors" | Production has no programmer errors. All are runtime. | **Return error, no panic()** |
| "Must-functions are convenient" | Convenience crashes production. | **Remove must-functions, propagate errors** |
| "log.Fatal is cleaner than error handling" | Clean code that crashes is not clean. | **Return error, handle in main()** |
| "This will never fail in production" | Never = always in production. | **Return error anyway** |
| "Tests use panic, why not production?" | Tests fail fast. Production must recover. | **Different rules for test vs production** |

---

## Function Design (MANDATORY)

**Single Responsibility Principle (SRP):** Each function MUST have exactly ONE responsibility.

### Rules

| Rule | Description |
|------|-------------|
| **One responsibility per function** | A function should do ONE thing and do it well |
| **Max 20-30 lines** | If longer, break into smaller functions |
| **One level of abstraction** | Don't mix high-level and low-level operations |
| **Descriptive names** | Function name should describe its single responsibility |

### Examples

```go
// ❌ BAD - Multiple responsibilities
func ProcessOrder(order Order) error {
    // Validate order
    if order.Items == nil {
        return errors.New("no items")
    }
    // Calculate total
    total := 0.0
    for _, item := range order.Items {
        total += item.Price * float64(item.Quantity)
    }
    // Apply discount
    if order.CouponCode != "" {
        total = total * 0.9
    }
    // Save to database
    db.Save(&order)
    // Send email
    sendEmail(order.CustomerEmail, "Order confirmed")
    return nil
}

// ✅ GOOD - Single responsibility per function
func ProcessOrder(order Order) error {
    if err := validateOrder(order); err != nil {
        return err
    }
    total := calculateTotal(order.Items)
    total = applyDiscount(total, order.CouponCode)
    if err := saveOrder(order, total); err != nil {
        return err
    }
    return notifyCustomer(order.CustomerEmail)
}

func validateOrder(order Order) error {
    if order.Items == nil || len(order.Items) == 0 {
        return errors.New("order must have items")
    }
    return nil
}

func calculateTotal(items []Item) float64 {
    total := 0.0
    for _, item := range items {
        total += item.Price * float64(item.Quantity)
    }
    return total
}

func applyDiscount(total float64, couponCode string) float64 {
    if couponCode != "" {
        return total * 0.9
    }
    return total
}
```

### Signs a Function Has Multiple Responsibilities

| Sign | Action |
|------|--------|
| Multiple `// section` comments | Split at comment boundaries |
| "and" in function name | Split into separate functions |
| More than 3 parameters | Consider parameter object or splitting |
| Nested conditionals > 2 levels | Extract inner logic to functions |
| Function does validation and processing | Separate validation function |

---

