## Safe Goroutines (cruntime)

All goroutines in production code **MUST** be launched via `cruntime.SafeGoWithContextAndComponent`. Raw `go func(){}()` is **FORBIDDEN**.

### MANDATORY Pattern

```go
cruntime.SafeGoWithContextAndComponent(
    ctx,
    logger,
    "component",       // e.g. "bootstrap", "auth", "worker"
    "goroutine-name",  // e.g. "server-runner", "cache-cleanup"
    cruntime.CrashProcess, // or cruntime.KeepRunning
    func(goCtx context.Context) {
        // goroutine body
    },
)
```

### Policies

| Policy | Behavior | Use When |
|--------|----------|----------|
| `cruntime.CrashProcess` | Logs panic + exits process | Critical goroutines (server, main loop) |
| `cruntime.KeepRunning` | Logs panic + continues | Background tasks (cache cleanup, polling) |

### FORBIDDEN vs CORRECT

```go
// FORBIDDEN: Raw goroutines in production code
go func() { ... }()  // No panic recovery, no context, no observability

// CORRECT: Always use cruntime
cruntime.SafeGoWithContextAndComponent(ctx, logger, "comp", "name", policy, fn)
```

---

