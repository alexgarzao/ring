## Standards Compliance Output Format

When producing a Standards Compliance report (used by ring:dev-refactor workflow), follow these output formats:

### If all Categories Are Compliant

```markdown
## Standards Compliance

### Lerian/Ring Standards Comparison

#### Bootstrap & Initialization
| Category | Current Pattern | Expected Pattern | Status | Evidence |
|----------|----------------|------------------|--------|----------|
| Config Struct | Nested `Config` struct with `envPrefix` tags | Nested structs with `envPrefix` tags | ✅ Compliant | `internal/bootstrap/config.go:15` |
| Config Loading | `libCommons.InitLocalEnvConfig()` + `env.Parse(&cfg)` | `libCommons.InitLocalEnvConfig()` + `env.Parse()` | ✅ Compliant | `internal/bootstrap/config.go:42` |
| Logger Init | `czap.New(czap.Config{...})` | `czap.New()` (bootstrap only) | ✅ Compliant | `internal/bootstrap/config.go:45` |
| Telemetry Init | `cotel.NewTelemetry()` + `tl.ApplyGlobals()` | `cotel.NewTelemetry()` + `ApplyGlobals()` | ✅ Compliant | `internal/bootstrap/config.go:48` |
| ... | ... | ... | ✅ Compliant | ... |

#### Context & Tracking
| Category | Current Pattern | Expected Pattern | Status | Evidence |
|----------|----------------|------------------|--------|----------|
| ... | ... | ... | ✅ Compliant | ... |

#### Infrastructure
| Category | Current Pattern | Expected Pattern | Status | Evidence |
|----------|----------------|------------------|--------|----------|
| ... | ... | ... | ✅ Compliant | ... |

#### Domain Patterns
| Category | Current Pattern | Expected Pattern | Status | Evidence |
|----------|----------------|------------------|--------|----------|
| ... | ... | ... | ✅ Compliant | ... |

### Verdict: ✅ FULLY COMPLIANT

No migration actions required. All categories verified against Lerian/Ring Go Standards.
```

### If any Category Is Non-Compliant

```markdown
## Standards Compliance

### Lerian/Ring Standards Comparison

#### Bootstrap & Initialization
| Category | Current Pattern | Expected Pattern | Status | File/Location |
|----------|----------------|------------------|--------|---------------|
| Config Struct | Scattered `os.Getenv()` calls | Nested structs with `envPrefix` tags | ⚠️ Non-Compliant | `cmd/api/main.go` |
| Config Loading | Manual env parsing | `libCommons.InitLocalEnvConfig()` + `env.Parse()` | ⚠️ Non-Compliant | `cmd/api/main.go:25` |
| Logger Init | `czap.New(czap.Config{...})` | `czap.New()` (bootstrap only) | ✅ Compliant | `cmd/api/main.go:30` |
| ... | ... | ... | ... | ... |

#### Context & Tracking
| Category | Current Pattern | Expected Pattern | Status | File/Location |
|----------|----------------|------------------|--------|---------------|
| ... | ... | ... | ... | ... |

### Verdict: ⚠️ NON-COMPLIANT (X of Y categories)

### Required Changes for Compliance

1. **Config Struct Migration**
   - Replace: Direct `os.Getenv()` calls scattered across files
   - With: Nested `Config` struct with `envPrefix` tags in `/internal/bootstrap/config.go`
   - Import: `libCommons "github.com/LerianStudio/lib-commons/v5/commons"`
   - Usage: `libCommons.InitLocalEnvConfig()` + `env.Parse(&cfg)`
   - Files affected: `cmd/api/main.go`, `internal/service/user.go`

2. **Logger Migration**
   - Replace: Custom logger or `log.Println()`
   - With: lib-commons v5 structured logger
   - Bootstrap import: `czap "github.com/LerianStudio/lib-commons/v5/commons/zap"` (initialization)
   - Application import: `clog "github.com/LerianStudio/lib-commons/v5/commons/log"` (interface for logging calls)
   - Bootstrap usage: `logger, err := czap.New(czap.Config{...})` (returns `clog.Logger` interface)
   - Application usage: `s.logger.Log(ctx, clog.LevelInfo, "msg", clog.String("key", "val"))`
   - Files affected: [list files]

3. **Telemetry Migration**
   - Replace: No tracing or custom tracing
   - With: OpenTelemetry integration via lib-commons v5
   - Import: `cotel "github.com/LerianStudio/lib-commons/v5/commons/opentelemetry"`
   - Usage: `tl, err := cotel.NewTelemetry(cotel.TelemetryConfig{...})` + `tl.ApplyGlobals()`
   - Files affected: [list files]

4. **[Next Category] Migration**
   - Replace: ...
   - With: ...
   - Import: ...
   - Usage: ...
```

**CRITICAL:** The comparison table is not optional. It serves as:
1. **Evidence** that each category was actually checked
2. **Documentation** for the codebase's compliance status
3. **Audit trail** for future refactors

---

