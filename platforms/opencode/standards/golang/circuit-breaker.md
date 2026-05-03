## Circuit Breaker (MANDATORY for External Calls)

All outbound calls to external services **MUST** use circuit breakers to prevent cascading failures.

### Using sony/gobreaker (Recommended for Adapters)

```go
import "github.com/sony/gobreaker/v2"

// Initialize per-adapter circuit breaker
cb := gobreaker.NewCircuitBreaker[any](gobreaker.Settings{
    Name:        "midaz-ledger",
    MaxRequests: 3,                    // half-open: allow 3 test requests
    Interval:    30 * time.Second,     // closed: reset counts every 30s
    Timeout:     30 * time.Second,     // open → half-open after 30s
    ReadyToTrip: func(counts gobreaker.Counts) bool {
        return counts.ConsecutiveFailures >= 5
    },
})

// Wrap external calls
result, err := cb.Execute(func() (any, error) {
    return httpClient.Do(req)
})
if err != nil {
    if errors.Is(err, gobreaker.ErrOpenState) {
        // Circuit is open — fail fast, do not call external service
        return nil, fmt.Errorf("service unavailable (circuit open): %w", err)
    }
    return nil, fmt.Errorf("external call failed: %w", err)
}
```

### Using lib-commons Circuit Breaker Manager

```go
import ccb "github.com/LerianStudio/lib-commons/v5/commons/circuitbreaker"

// Create manager for multiple breakers
manager := ccb.NewManager(logger)

// Register breakers with preset configs
manager.Register("midaz", ccb.HTTPServiceConfig())
manager.Register("crm", ccb.ConservativeConfig())
manager.Register("jd-spb", ccb.AggressiveConfig())

// Execute with breaker
result, err := manager.Execute("midaz", func() (any, error) {
    return client.Call(ctx, req)
})
```

### Preset Configurations

| Preset | Max Failures | Timeout | Use When |
|--------|-------------|---------|----------|
| `DefaultConfig()` | 5 | 30s | General purpose |
| `AggressiveConfig()` | 3 | 15s | Fast failure detection (payment gateways) |
| `ConservativeConfig()` | 10 | 60s | High tolerance (batch jobs) |
| `HTTPServiceConfig()` | 5 | 30s | HTTP service-to-service calls |
| `DatabaseConfig()` | 3 | 45s | Database connections |

### Health Checker Integration

```go
// Automatic health probes with recovery
healthChecker := ccb.NewHealthChecker(manager, 10*time.Second, 5*time.Second, logger)
healthChecker.Register("midaz", func(ctx context.Context) error {
    return client.Ping(ctx)
})
healthChecker.Start(ctx)
defer healthChecker.Stop()
```

### Adapter Error Pattern

```go
// Convert breaker errors to domain-specific adapter errors
type AdapterError struct {
    AdapterName string
    Code        string // e.g. "SVC-1000" (service unavailable)
    Operation   string
    Err         error
}

func (e *AdapterError) Error() string {
    return fmt.Sprintf("[%s] %s %s: %s", e.Code, e.AdapterName, e.Operation, e.Err)
}

func (e *AdapterError) Unwrap() error { return e.Err }
```

### What not to Do

```go
// FORBIDDEN: External calls without circuit breaker
resp, err := http.Get("http://external-service/api")  // No protection

// FORBIDDEN: Global circuit breaker for all services
var globalBreaker = gobreaker.NewCircuitBreaker(...)  // Each service needs its own

// CORRECT: Per-adapter breaker with appropriate config
midazBreaker := gobreaker.NewCircuitBreaker[any](gobreaker.Settings{Name: "midaz", ...})
crmBreaker := gobreaker.NewCircuitBreaker[any](gobreaker.Settings{Name: "crm", ...})
```

---

