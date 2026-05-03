## Checklist

Before submitting Go code, verify:

- [ ] Using lib-commons v5 for infrastructure
- [ ] Configuration loaded via `libCommons.InitLocalEnvConfig()` + `env.Parse()` with nested config structs
- [ ] Telemetry initialized via `cotel.NewTelemetry()` + `tl.ApplyGlobals()`
- [ ] Logger initialized via `czap.New()` and dependency-injected (not recovered from context)
- [ ] **No direct imports of `go.opentelemetry.io/otel/*` packages** (use lib-commons wrappers)
- [ ] **No raw goroutines** (`go func(){}()`) - use `cruntime.SafeGoWithContextAndComponent`
- [ ] Domain validation uses `cassert` (returns errors, NEVER panics)
- [ ] Structured logging uses `s.logger.Log(ctx, level, "msg", clog.String(...))` pattern
- [ ] All errors are checked and wrapped with context
- [ ] Error codes use service prefix (e.g., PLT-0001)
- [ ] No `panic()` in business logic - `InitServersWithOptions` returns errors
- [ ] Tests use table-driven pattern
- [ ] Database models have ToEntity/FromEntity methods
- [ ] Interfaces defined where they're used
- [ ] No global mutable state
- [ ] Context propagated through all calls
- [ ] Sensitive data not logged
- [ ] golangci-lint passes
- [ ] Pagination strategy defined in TRD (or confirmed with user if no TRD)
- [ ] Using `csafe.Divide()` for financial calculations (never raw division)
- [ ] Sensitive fields encrypted with `ccrypto` (AES-GCM)
- [ ] Retry logic uses `cbackoff.Exponential()` with jitter
- [ ] Custom metrics defined with `cmetrics.Metric` struct
- [ ] External service calls wrapped in circuit breakers
