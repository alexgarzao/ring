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
// CORRECT: Logger is dependency-injected (struct field)
// s.logger clog.Logger  (injected at construction time)

// CORRECT: Log with typed fields (v5 pattern)
s.logger.Log(ctx, clog.LevelInfo, "Processing entity",
    clog.String("entity_id", entityID))
s.logger.Log(ctx, clog.LevelWarn, "Rate limit approaching",
    clog.Int("current", current), clog.Int("limit", limit))
s.logger.Log(ctx, clog.LevelError, "Failed to save entity",
    clog.Err(err))
```

### Migration Examples

```go
// ❌ FORBIDDEN: fmt.Println
fmt.Println("Starting server...")

// ✅ REQUIRED: lib-commons logger with typed fields
s.logger.Log(ctx, clog.LevelInfo, "Starting server",
    clog.String("address", s.serverAddress))

// ❌ FORBIDDEN: fmt.Printf
fmt.Printf("Processing user: %s\n", userID)

// ✅ REQUIRED: lib-commons logger with typed fields
s.logger.Log(ctx, clog.LevelInfo, "Processing user",
    clog.String("user_id", userID))

// ❌ FORBIDDEN: log.Printf
log.Printf("[ERROR] Failed to connect: %v", err)

// ✅ REQUIRED: lib-commons logger with span error
s.logger.Log(ctx, clog.LevelError, "Failed to connect",
    clog.Err(err))
cotel.HandleSpanError(&span, "Connection failed", err)

// ❌ FORBIDDEN: log.Fatal (breaks graceful shutdown)
log.Fatal("Cannot start without config")

// ✅ REQUIRED: return error from InitServersWithOptions (v5 pattern)
return nil, fmt.Errorf("cannot start without config: %w", err)
```

### What not to Log (Sensitive Data)

```go
// FORBIDDEN - sensitive data in structured fields
s.logger.Log(ctx, clog.LevelInfo, "user login", clog.String("password", password))  // NEVER
s.logger.Log(ctx, clog.LevelInfo, "payment", clog.String("card_number", card))      // NEVER
s.logger.Log(ctx, clog.LevelInfo, "auth", clog.String("token", token))              // NEVER
s.logger.Log(ctx, clog.LevelInfo, "user", clog.String("cpf", cpf))                  // NEVER (PII)
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

