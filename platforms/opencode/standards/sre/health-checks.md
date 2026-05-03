## Health Checks

### Required Endpoints

### Implementation

```go
// Go implementation for observability
type ObservabilityChecker struct {
    db    *sql.DB
    redis *redis.Client
}

// Liveness - is the process alive?
func (h *HealthChecker) LivenessHandler(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    w.Write([]byte("OK"))
}

// Readiness - can we serve traffic?
func (h *HealthChecker) ReadinessHandler(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
    defer cancel()

    checks := []struct {
        name string
        fn   func(context.Context) error
    }{
        {"database", func(ctx context.Context) error { return h.db.PingContext(ctx) }},
        {"redis", func(ctx context.Context) error { return h.redis.Ping(ctx).Err() }},
    }

    var failures []string
    for _, check := range checks {
        if err := check.fn(ctx); err != nil {
            failures = append(failures, fmt.Sprintf("%s: %v", check.name, err))
        }
    }

    if len(failures) > 0 {
        w.WriteHeader(http.StatusServiceUnavailable)
        json.NewEncoder(w).Encode(map[string]interface{}{
            "status":  "unhealthy",
            "checks":  failures,
        })
        return
    }

    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]interface{}{
        "status": "healthy",
    })
}
```

### Kubernetes Configuration

```yaml
# Observability configuration
# JSON structured logging required
# OpenTelemetry tracing recommended for distributed systems
```

---

