# Go Standards - Architecture

> **Module:** architecture.md | **Sections:** §23-27 | **Parent:** [index.md](index.md)

This module covers architecture patterns, directory structure, concurrency, goroutine recovery, and query optimization.

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [Architecture Patterns](#architecture-patterns) | Hexagonal architecture and interface-based abstractions |
| 2 | [Directory Structure](#directory-structure) | Lerian pattern directory layout |
| 3 | [Concurrency Patterns](#concurrency-patterns) | Goroutines with context and channel patterns |
| 4 | [Goroutine Recovery Patterns](#goroutine-recovery-patterns-mandatory) | Panic recovery for background goroutines |
| 5 | [N+1 Query Detection](#n1-query-detection-mandatory) | Avoiding N+1 queries in collection processing |

---

## Architecture Patterns

### Hexagonal Architecture (Ports & Adapters)

```text
/internal
  /bootstrap         # Application initialization
    config.go
    fiber.server.go
  /domain            # Business entities (no dependencies)
    user.go
    errors.go
  /services          # Application/Business logic
    /command         # Write operations
    /query           # Read operations
  /adapters          # Implementations (adapters)
    /http/in         # HTTP handlers + routes
    /grpc/in         # gRPC handlers
    /postgres        # PostgreSQL repositories
    /mongodb         # MongoDB repositories
    /redis           # Redis repositories
```

### Interface-Based Abstractions

```go
// Define interface in the package that USES it (not implements)
// /internal/services/command/usecase.go

type UserRepository interface {
    FindByID(ctx context.Context, id uuid.UUID) (*domain.User, error)
    Save(ctx context.Context, user *domain.User) error
}

type UseCase struct {
    UserRepo UserRepository  // Depend on interface
}
```

---

## Directory Structure

The directory structure follows the **Lerian pattern** - a simplified hexagonal architecture without explicit DDD folders.

```text
/cmd
  /app                   # Main application entry
    main.go
/internal
  /bootstrap             # Initialization (config, servers)
    config.go
    fiber.server.go
    grpc.server.go       # (if service uses gRPC)
    rabbitmq.server.go   # (if service uses RabbitMQ)
    service.go
  /services              # Business logic
    /command             # Write operations (use cases)
    /query               # Read operations (use cases)
  /adapters              # Infrastructure implementations
    /http/in             # HTTP handlers + routes
    /grpc/in             # gRPC handlers
    /grpc/out            # gRPC clients
    /postgres            # PostgreSQL repositories
    /mongodb             # MongoDB repositories
    /redis               # Redis repositories
    /rabbitmq            # RabbitMQ producers/consumers
/pkg
  /constant              # Constants and error codes
  /mmodel                # Shared models
  /net/http              # HTTP utilities
/api                     # OpenAPI/Swagger specs
/migrations              # Database migrations
```

**Key differences from traditional DDD:**
- **No `/internal/domain` folder** - Business entities live in `/pkg/mmodel` or within service files
- **Services are the core** - `/internal/services` contains all business logic (command/query pattern)
- **Adapters are flat** - Database repositories are organized by technology, not by domain

---

## Concurrency Patterns

### Goroutines with Context

```go
func processItems(ctx context.Context, items []Item) error {
    g, ctx := errgroup.WithContext(ctx)

    for _, item := range items {
        item := item // capture variable
        g.Go(func() error {
            select {
            case <-ctx.Done():
                return ctx.Err()
            default:
                return processItem(ctx, item)
            }
        })
    }

    return g.Wait()
}
```

### Channel Patterns

```go
// Worker pool
func workerPool(ctx context.Context, jobs <-chan Job, results chan<- Result) {
    for {
        select {
        case <-ctx.Done():
            return
        case job, ok := <-jobs:
            if !ok {
                return
            }
            results <- process(job)
        }
    }
}
```

---

## Goroutine Recovery Patterns (MANDATORY)

**Production Findings:**
- HP-9: Goroutine without recovery kills entire process
- P2-3: Recovery middleware needed for all background goroutines

**⛔ HARD GATE:** All goroutines started with `go` keyword MUST have panic recovery. Unrecovered panics in goroutines crash the entire process.

### Why Recovery Is MANDATORY

| Scenario | Without Recovery | With Recovery |
|----------|------------------|---------------|
| Panic in goroutine | Process crashes | Error logged, goroutine terminates gracefully |
| nil pointer | Pod restart loop | Error captured, other goroutines unaffected |
| Divide by zero | Service down | Incident logged, service continues |

### Recovery Wrapper Pattern (REQUIRED)

```go
// pkg/recovery/recovery.go
package recovery

import (
    "context"
    "runtime/debug"

    libCommons "github.com/LerianStudio/lib-commons/v2/commons"
)

// Go wraps a goroutine with panic recovery
// MUST use this instead of bare `go func()` for all background goroutines
func Go(ctx context.Context, fn func()) {
    logger, _, _, _ := libCommons.NewTrackingFromContext(ctx)

    go func() {
        defer func() {
            if r := recover(); r != nil {
                stack := string(debug.Stack())
                logger.Errorf("Goroutine panic recovered: %v\nStack: %s", r, stack)
                // Optional: Send to error tracking (Sentry, etc.)
            }
        }()
        fn()
    }()
}

// GoWithError wraps a goroutine that returns an error
func GoWithError(ctx context.Context, fn func() error, errChan chan<- error) {
    logger, _, _, _ := libCommons.NewTrackingFromContext(ctx)

    go func() {
        defer func() {
            if r := recover(); r != nil {
                stack := string(debug.Stack())
                logger.Errorf("Goroutine panic recovered: %v\nStack: %s", r, stack)
                errChan <- fmt.Errorf("goroutine panicked: %v", r)
            }
        }()

        if err := fn(); err != nil {
            errChan <- err
        }
    }()
}
```

### Usage Pattern

```go
// ✅ CORRECT: Using recovery wrapper
recovery.Go(ctx, func() {
    processBackgroundTask(ctx, item)
})

// ✅ CORRECT: With error handling
errChan := make(chan error, 1)
recovery.GoWithError(ctx, func() error {
    return processItem(ctx, item)
}, errChan)

// ✅ CORRECT: Inline recovery for simple cases
go func() {
    defer func() {
        if r := recover(); r != nil {
            logger.Errorf("Panic in goroutine: %v", r)
        }
    }()
    doWork()
}()
```

### FORBIDDEN Patterns

```go
// ❌ FORBIDDEN: Bare goroutine without recovery
go processBackgroundTask(ctx, item)  // WRONG: no recovery

// ❌ FORBIDDEN: Fire-and-forget goroutine
go func() {
    result := heavyComputation()  // WRONG: panic crashes process
    sendResult(result)
}()

// ❌ FORBIDDEN: Assuming "it won't panic"
go handleWebhook(payload)  // WRONG: any nil pointer kills the process
```

### Detection Commands

```bash
# Find bare goroutines without recovery
grep -rn "^\s*go func\|^\s*go [a-zA-Z]" internal/ pkg/ --include="*.go" | grep -v "_test.go"

# Review each match - ensure recovery wrapper or inline defer/recover exists
# Expected: All goroutines use recovery.Go() or have explicit defer recover()
```

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Goroutines won't panic" | All code can panic. nil pointer, slice bounds, map access. | **Add recovery wrapper** |
| "Main goroutine will catch it" | Panics in goroutines don't propagate to main. | **Add recovery per goroutine** |
| "Process will restart" | Restart = downtime + lost in-flight work. | **Recover and log instead** |
| "It's just a background task" | Background task crash = process crash. | **Add recovery wrapper** |
| "Recovery adds overhead" | Overhead is negligible vs process crash cost. | **Add recovery wrapper** |

---

## N+1 Query Detection (MANDATORY)

**Production Finding (P2-7):** N+1 queries cause database connection exhaustion and latency spikes under load.

**⛔ HARD GATE:** Queries inside loops are FORBIDDEN. MUST use batch loading, eager loading, or JOINs.

### What Is N+1 Problem

```text
N+1 = 1 query to get list + N queries for each item

Example: Get 100 orders with customer names
- BAD: 1 query for orders + 100 queries for customers = 101 queries
- GOOD: 1 query for orders + 1 query for customers (batch) = 2 queries
```

### FORBIDDEN Pattern

```go
// ❌ FORBIDDEN: Query inside loop (N+1)
func (r *OrderRepository) GetOrdersWithCustomers(ctx context.Context) ([]OrderWithCustomer, error) {
    orders, err := r.db.Query(ctx, "SELECT * FROM orders LIMIT 100")
    if err != nil {
        return nil, err
    }

    var results []OrderWithCustomer
    for _, order := range orders {
        // WRONG: This executes 100 times (N+1)
        customer, err := r.db.QueryRow(ctx, "SELECT * FROM customers WHERE id = $1", order.CustomerID)
        if err != nil {
            return nil, err
        }
        results = append(results, OrderWithCustomer{Order: order, Customer: customer})
    }
    return results, nil
}
```

### Correct Patterns (REQUIRED)

#### Option 1: JOIN Query

```go
// ✅ CORRECT: Single query with JOIN
func (r *OrderRepository) GetOrdersWithCustomers(ctx context.Context) ([]OrderWithCustomer, error) {
    query := `
        SELECT o.id, o.total, o.created_at, c.id, c.name, c.email
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LIMIT 100
    `
    rows, err := r.db.Query(ctx, query)
    // ... scan results
}
```

#### Option 2: Batch Loading

```go
// ✅ CORRECT: Batch load with IN clause
func (r *OrderRepository) GetOrdersWithCustomers(ctx context.Context) ([]OrderWithCustomer, error) {
    // Step 1: Get orders
    orders, err := r.db.Query(ctx, "SELECT * FROM orders LIMIT 100")
    if err != nil {
        return nil, err
    }

    // Step 2: Collect unique customer IDs
    customerIDs := make([]uuid.UUID, 0, len(orders))
    for _, o := range orders {
        customerIDs = append(customerIDs, o.CustomerID)
    }

    // Step 3: Batch load customers (1 query, not N)
    customers, err := r.db.Query(ctx, "SELECT * FROM customers WHERE id = ANY($1)", customerIDs)
    if err != nil {
        return nil, err
    }

    // Step 4: Build lookup map
    customerMap := make(map[uuid.UUID]Customer)
    for _, c := range customers {
        customerMap[c.ID] = c
    }

    // Step 5: Combine results
    var results []OrderWithCustomer
    for _, o := range orders {
        results = append(results, OrderWithCustomer{
            Order:    o,
            Customer: customerMap[o.CustomerID],
        })
    }
    return results, nil
}
```

### Detection Commands

```bash
# Find potential N+1 patterns (queries inside loops)
grep -rn "for.*range" internal/adapters/postgres --include="*.go" -A 10 | grep -E "Query|Exec|Select"

# Find loop + query combinations
grep -rn "for.*{" internal/adapters --include="*.go" -A 15 | grep -E "\.Query\(|\.Exec\(|\.Get\(|\.Select\("

# Review each match - if query is inside loop: VIOLATION
```

### Query Count Guidelines

| Collection Size | Max Queries | Strategy |
|-----------------|-------------|----------|
| 1-10 items | 2 | Batch or JOIN |
| 10-100 items | 2 | Batch with IN clause |
| 100+ items | 2 | Batch with pagination |
| Any size | Never N+1 | JOIN or batch always |

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Only a few records" | Few now = many later. N+1 scales poorly. | **Use batch/JOIN** |
| "Query is fast" | 1ms * 1000 = 1s. Latency compounds. | **Use batch/JOIN** |
| "Database handles it" | DB connection pool exhausts under load. | **Use batch/JOIN** |
| "ORM optimizes it" | ORMs don't auto-optimize N+1. You must. | **Explicit batch/JOIN** |
| "Caching helps" | Cache miss = N+1. Cold start = N+1. | **Use batch/JOIN** |

---

