## OpenTelemetry with lib-commons (MANDATORY for Go)

All Go services **MUST** integrate OpenTelemetry using `lib-commons/v5`. This ensures consistent observability patterns across all Lerian Studio services.

> **Reference**: See `dev-team/docs/standards/golang.md` for complete lib-commons integration patterns.

### Required Imports

```go
import (
    libCommons "github.com/LerianStudio/lib-commons/v5/commons"
    libZap "github.com/LerianStudio/lib-commons/v5/commons/zap"           // Logger initialization (bootstrap only)
    libLog "github.com/LerianStudio/lib-commons/v5/commons/log"           // Logger interface (services, routes, consumers)
    libOpentelemetry "github.com/LerianStudio/lib-commons/v5/commons/opentelemetry"
    libHTTP "github.com/LerianStudio/lib-commons/v5/commons/net/http"
    libServer "github.com/LerianStudio/lib-commons/v5/commons/server"
)
```

### Telemetry Flow (MANDATORY)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. BOOTSTRAP (config.go)                                        │
│    telemetry := libOpentelemetry.InitializeTelemetry(&config)   │
│    → Creates OpenTelemetry provider once at startup             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. ROUTER (routes.go)                                           │
│    tlMid := libHTTP.NewTelemetryMiddleware(tl)                  │
│    f.Use(tlMid.WithTelemetry(tl))      ← Injects into context   │
│    ...routes...                                                  │
│    f.Use(tlMid.EndTracingSpans)        ← Closes root spans      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. any layer (handlers, services, repositories)                 │
│    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)│
│    ctx, span := tracer.Start(ctx, "operation_name")             │
│    defer span.End()                                              │
│    logger.Infof("Processing...")   ← Logger from same context   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. SERVER LIFECYCLE (fiber.server.go)                           │
│    libServer.NewServerManager(nil, &s.telemetry, s.logger)      │
│        .WithHTTPServer(s.app, s.serverAddress)                  │
│        .StartWithGracefulShutdown()                             │
│    → Handles signal trapping + telemetry flush + clean shutdown │
└─────────────────────────────────────────────────────────────────┘
```

### 1. Bootstrap Initialization (MANDATORY)

```go
// bootstrap/config.go
func InitServers() (*Service, error) {
    cfg := &Config{}
    if err := libCommons.SetConfigFromEnvVars(cfg); err != nil {
        return nil, fmt.Errorf("failed to load config: %w", err)
    }

    // Initialize logger FIRST (zap package for initialization in bootstrap)
    logger := libZap.InitializeLogger()

    // Initialize telemetry with config
    telemetry := libOpentelemetry.InitializeTelemetry(&libOpentelemetry.TelemetryConfig{
        LibraryName:               cfg.OtelLibraryName,
        ServiceName:               cfg.OtelServiceName,
        ServiceVersion:            cfg.OtelServiceVersion,
        DeploymentEnv:             cfg.OtelDeploymentEnv,
        CollectorExporterEndpoint: cfg.OtelColExporterEndpoint,
        EnableTelemetry:           cfg.EnableTelemetry,
        Logger:                    logger,
    })

    // Pass telemetry to router...
}
```

### 2. Router Middleware Setup (MANDATORY)

```go
// adapters/http/in/routes.go
func NewRouter(lg libLog.Logger, tl *libOpentelemetry.Telemetry, ...) *fiber.App {
    f := fiber.New(fiber.Config{
        DisableStartupMessage: true,
        ErrorHandler: func(ctx *fiber.Ctx, err error) error {
            return libHTTP.HandleFiberError(ctx, err)
        },
    })

    // Create telemetry middleware
    tlMid := libHTTP.NewTelemetryMiddleware(tl)

    // MUST be first middleware - injects tracer+logger into context
    f.Use(tlMid.WithTelemetry(tl))
    f.Use(libHTTP.WithHTTPLogging(libHTTP.WithCustomLogger(lg)))

    // ... define routes ...

    // Version endpoint
    f.Get("/version", libHTTP.Version)

    // MUST be last middleware - closes root spans
    f.Use(tlMid.EndTracingSpans)

    return f
}
```

### 3. Recovering Logger & Core three (MANDATORY)

```go
// any file in any layer (handler, service, repository)
func (s *Service) ProcessEntity(ctx context.Context, id string) error {
    // Single call recovers BOTH logger and tracer from context
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    // Create child span for this operation
    ctx, span := tracer.Start(ctx, "service.process_entity")
    defer span.End()

    // Logger is automatically correlated with trace
    logger.Infof("Processing entity: %s", id)

    // Pass ctx to downstream calls - trace propagates automatically
    return s.repo.Update(ctx, id)
}
```

### 4. Error Handling with Spans (MANDATORY)

```go
// For technical errors (unexpected failures)
if err != nil {
    libOpentelemetry.HandleSpanError(&span, "Failed to connect database", err)
    logger.Errorf("Database error: %v", err)
    return nil, err
}

// For business errors (expected validation failures)
if err != nil {
    libOpentelemetry.HandleSpanBusinessErrorEvent(&span, "Validation failed", err)
    logger.Warnf("Validation error: %v", err)
    return nil, err
}
```

### 5. Server Lifecycle with Graceful Shutdown (MANDATORY)

```go
// bootstrap/fiber.server.go
type Server struct {
    app           *fiber.App
    serverAddress string
    logger        libLog.Logger
    telemetry     libOpentelemetry.Telemetry
}

func (s *Server) Run(l *libCommons.Launcher) error {
    libServer.NewServerManager(nil, &s.telemetry, s.logger).
        WithHTTPServer(s.app, s.serverAddress).
        StartWithGracefulShutdown()  // Handles: SIGINT/SIGTERM, telemetry flush, connections close
    return nil
}
```

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OTEL_RESOURCE_SERVICE_NAME` | Service name in traces | `service-name` |
| `OTEL_LIBRARY_NAME` | Library identifier | `service-name` |
| `OTEL_RESOURCE_SERVICE_VERSION` | Service version | `1.0.0` |
| `OTEL_RESOURCE_DEPLOYMENT_ENVIRONMENT` | Environment | `production` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Collector endpoint | `http://otel-collector:4317` |
| `ENABLE_TELEMETRY` | Enable/disable | `true` |

### lib-commons Telemetry Checklist

| Check | What to Verify | Status |
|-------|----------------|--------|
| Bootstrap Init | `libOpentelemetry.InitializeTelemetry()` called in bootstrap | Required |
| Middleware Order | `WithTelemetry()` is FIRST, `EndTracingSpans` is LAST | Required |
| Context Recovery | All layers use `libCommons.NewTrackingFromContext(ctx)` | Required |
| Span Creation | Operations create spans via `tracer.Start(ctx, "name")` | Required |
| Error Handling | Uses `HandleSpanError` or `HandleSpanBusinessErrorEvent` | Required |
| Graceful Shutdown | `libServer.NewServerManager().StartWithGracefulShutdown()` | Required |
| Env Variables | All OTEL_* variables configured | Required |

### What not to Do

```go
// FORBIDDEN: Manual OpenTelemetry setup without lib-commons
import "go.opentelemetry.io/otel"
tp := trace.NewCore threeProvider(...)  // DON'T do this manually

// FORBIDDEN: Creating loggers without context
logger := zap.NewLogger()  // DON'T do this in services

// FORBIDDEN: Not passing context to downstream calls
s.repo.Update(id)  // DON'T forget context

// CORRECT: Always use lib-commons patterns
telemetry := libOpentelemetry.InitializeTelemetry(&config)
logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)
s.repo.Update(ctx, id)  // Context propagates trace
```

### Standards Compliance Categories

When evaluating a codebase for lib-commons telemetry compliance, check these categories:

| Category | Expected Pattern | Evidence Location |
|----------|------------------|-------------------|
| Telemetry Init | `libOpentelemetry.InitializeTelemetry()` | `internal/bootstrap/config.go` |
| Logger Init | `libZap.InitializeLogger()` (bootstrap only) | `internal/bootstrap/config.go` |
| Middleware Setup | `NewTelemetryMiddleware()` + `WithTelemetry()` | `internal/adapters/http/in/routes.go` |
| Middleware Order | `WithTelemetry` first, `EndTracingSpans` last | `internal/adapters/http/in/routes.go` |
| Context Recovery | `libCommons.NewTrackingFromContext(ctx)` | All handlers, services, repositories |
| Span Creation | `tracer.Start(ctx, "operation")` | All significant operations |
| Error Spans | `HandleSpanError` / `HandleSpanBusinessErrorEvent` | Error handling paths |
| Graceful Shutdown | `libServer.NewServerManager().StartWithGracefulShutdown()` | `internal/bootstrap/fiber.server.go` |

---

