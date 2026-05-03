## Observability

All services **MUST** integrate OpenTelemetry using lib-commons.

### Distributed Tracing Architecture

Understanding how traces propagate is critical for proper instrumentation.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INCOMING HTTP REQUEST                                │
│                                                                             │
│  Headers: traceparent, tracestate (W3C Trace Context)                       │
│  - If present: child span created with remote parent (distributed trace)   │
│  - If absent: new root trace created                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  MIDDLEWARE: OTel middleware from chttp - CREATES ROOT SPAN                  │
│                                                                             │
│  What the OTel middleware does:                                              │
│  1. Extracts traceparent/tracestate from incoming headers                    │
│     → Uses otel.GetTextMapPropagator().Extract() for W3C trace context      │
│     → If traceparent exists: creates child span of remote parent            │
│     → If no traceparent: creates new root span                              │
│  2. tracer.Start(ctx, "GET /api/resource") - creates HTTP ROOT SPAN         │
│  3. Sets span attributes: http.method, http.url, http.route, etc.           │
│  4. Injects tracer, logger, and metrics factory into context                │
│  5. c.SetUserContext(ctx) - makes enriched context available to handlers    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  HANDLER LAYER (optional child spans - for complex handlers)                │
│                                                                             │
│  // Logger is dependency-injected; tracer via global wrapper                │
│  ctx, span := telemetry.StartSpan(ctx, "handler.create_tenant")             │
│  defer span.End()                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  SERVICE LAYER (MANDATORY child spans for all methods)                      │
│                                                                             │
│  // Logger is dependency-injected; tracer via global wrapper                │
│  ctx, span := telemetry.StartSpan(ctx, "service.tenant.create")             │
│  defer span.End()                                                           │
│                                                                             │
│  // Structured logging with fields (v5 pattern)                             │
│  s.logger.Log(ctx, clog.LevelInfo, "Creating tenant",                       │
│      clog.String("name", req.Name))                                         │
│                                                                             │
│  // Business errors → span status stays OK                                  │
│  telemetry.HandleSpanError(span, err) // for technical errors               │
│  telemetry.SetSpanSuccess(span)       // for success                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  REPOSITORY LAYER (optional - for complex database operations)              │
│                                                                             │
│  Same pattern as service layer                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  OUTGOING CALLS (HTTP, gRPC, Queue) - PROPAGATE TRACE CONTEXT               │
│                                                                             │
│  // HTTP Client: Inject traceparent/tracestate into outgoing headers        │
│  cotel.InjectHTTPContext(&req.Header, ctx)                                  │
│                                                                             │
│  // gRPC Client: Inject into outgoing metadata                              │
│  ctx = cotel.InjectGRPCContext(ctx)                                         │
│                                                                             │
│  // Queue/Message: Inject into message headers for async trace continuation │
│  headers := cotel.PrepareQueueHeaders(ctx, baseHeaders)                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Complete Telemetry Flow (Bootstrap to Shutdown)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. BOOTSTRAP (config.go)                                        │
│    tl, err := cotel.NewTelemetry(cotel.TelemetryConfig{...})   │
│    tl.ApplyGlobals()                                            │
│    → Creates OpenTelemetry provider once at startup             │
│    → Sets global TextMapPropagator for W3C TraceContext         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. ROUTER (routes.go)                                           │
│    Middleware chain:                                              │
│    recover → requestid → security headers → rate limiting        │
│    → CORS → sandbox → OTel → tenant → org validation → license  │
│    OTel middleware creates root span per request                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. any LAYER (handlers, services, repositories)                 │
│    // Logger is DI field; tracer via global wrapper              │
│    ctx, span := telemetry.StartSpan(ctx, "operation_name")      │
│    defer span.End()                                              │
│    s.logger.Log(ctx, clog.LevelInfo, "Processing...",           │
│        clog.String("key", "value"))                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. SERVER LIFECYCLE (service.go)                                 │
│    svc.Run(ctx) starts HTTP server via cruntime.SafeGo...       │
│    svc.Shutdown(ctx) flushes telemetry + drains connections      │
│    → main.go uses signal.NotifyContext for graceful shutdown     │
└─────────────────────────────────────────────────────────────────┘
```

---

### Service Method Instrumentation Checklist (MANDATORY)

**Every service method MUST implement these steps:**

| # | Step | Code Pattern | Purpose |
|---|------|--------------|---------|
| 1 | Logger as struct field | `s.logger clog.Logger` (dependency-injected) | Injected at construction time |
| 2 | Create child span | `ctx, span := telemetry.StartSpan(ctx, "service.{domain}.{operation}")` | Create traceable operation via global wrapper |
| 3 | Defer span end | `defer span.End()` | Ensure span closes even on panic |
| 4 | Use structured logger with fields | `s.logger.Log(ctx, clog.LevelInfo, "msg", clog.String("key", "val"))` | Logs correlated with trace |
| 5 | Handle business errors | `cotel.HandleSpanBusinessErrorEvent(&span, msg, err)` | Expected errors (validation, not found) |
| 6 | Handle technical errors | `cotel.HandleSpanError(&span, msg, err)` | Unexpected errors (DB, network) |
| 7 | Pass ctx downstream | All calls receive `ctx` with span | Trace propagation |

---

### Error Handling Classification

| Error Type | Examples | Handler Function | Span Status |
|------------|----------|------------------|-------------|
| **Business Error** | Validation failed, Resource not found, Conflict, Unauthorized | `cotel.HandleSpanBusinessErrorEvent` | OK (adds event) |
| **Technical Error** | DB connection failed, Timeout, Network error, Unexpected panic | `cotel.HandleSpanError` | ERROR (records error) |

**Why the distinction matters:**
- Business errors are expected and don't indicate system problems
- Technical errors indicate infrastructure issues requiring investigation
- Alerting systems typically trigger on ERROR status spans

---

### Complete Instrumented Service Method Template

```go
func (s *myService) DoSomething(ctx context.Context, req *Request) (*Response, error) {
    // 1. Logger is a struct field (dependency-injected at construction)
    // Core three is accessed via global wrapper (set by cotel.ApplyGlobals at bootstrap)

    // 2. Create child span for this operation
    ctx, span := telemetry.StartSpan(ctx, "service.my_service.do_something")
    defer span.End()

    // 3. Structured logging with typed fields (v5 pattern)
    s.logger.Log(ctx, clog.LevelInfo, "Processing request",
        clog.String("id", req.ID))

    // 4. Input validation - BUSINESS error (expected, span stays OK)
    if req.Name == "" {
        s.logger.Log(ctx, clog.LevelWarn, "Validation failed: empty name")
        cotel.HandleSpanBusinessErrorEvent(&span, "Validation failed", ErrInvalidInput)
        return nil, fmt.Errorf("%w: name is required", ErrInvalidInput)
    }

    // 5. External call - pass ctx to propagate trace context
    result, err := s.repo.Create(ctx, entity)
    if err != nil {
        // Check if it's a "not found" type error (business) vs DB failure (technical)
        if errors.Is(err, ErrNotFound) {
            s.logger.Log(ctx, clog.LevelWarn, "Entity not found",
                clog.String("id", req.ID))
            cotel.HandleSpanBusinessErrorEvent(&span, "Entity not found", err)
            return nil, err
        }

        // TECHNICAL error - unexpected failure, span marked ERROR
        s.logger.Log(ctx, clog.LevelError, "Failed to create entity",
            clog.Err(err))
        cotel.HandleSpanError(&span, "Repository create failed", err)
        return nil, fmt.Errorf("failed to create: %w", err)
    }

    s.logger.Log(ctx, clog.LevelInfo, "Entity created successfully",
        clog.String("id", result.ID))
    return result, nil
}
```

---

### Telemetry Wrapper Package (MANDATORY)

Every service MUST create a thin telemetry wrapper at `internal/shared/telemetry/tracer.go`. This wrapper accesses the global tracer (registered by `cotel.NewTelemetry()` + `tl.ApplyGlobals()` at bootstrap) and provides domain-specific helpers.

```go
// internal/shared/telemetry/tracer.go
package telemetry

import (
    "context"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/codes"
    "go.opentelemetry.io/otel/trace"
)

// tracerName identifies this service in distributed traces.
const tracerName = "github.com/LerianStudio/your-service"

// StartSpan creates a new span using the global tracer provider.
func StartSpan(ctx context.Context, name string, opts ...trace.SpanStartOption) (context.Context, trace.Span) {
    return otel.Core three(tracerName).Start(ctx, name, opts...)
}

// HandleSpanError records an error on the span and sets status to Error.
func HandleSpanError(span trace.Span, err error) {
    if span == nil || err == nil {
        return
    }
    span.RecordError(err)
    span.SetStatus(codes.Error, err.Error())
}

// SetSpanSuccess sets the span status to OK.
func SetSpanSuccess(span trace.Span) {
    if span == nil {
        return
    }
    span.SetStatus(codes.Ok, "")
}

// SpanFromContext returns the current span from context.
func SpanFromContext(ctx context.Context) trace.Span {
    return trace.SpanFromContext(ctx)
}
```

**Why a wrapper instead of direct `otel.Core three()` calls:**
- Single place to change the `tracerName` constant
- Domain-specific helpers (`HandleSpanError`, `SetSpanSuccess`) reduce boilerplate
- The wrapper uses the global provider set by `cotel.ApplyGlobals()` — no struct injection needed for tracer

**Span Naming Conventions:**

| Layer | Pattern | Examples |
|-------|---------|----------|
| HTTP Handler | `handler.{resource}.{action}` | `handler.tenant.create`, `handler.agent.list` |
| Service | `service.{domain}.{operation}` | `service.tenant.create`, `service.agent.register` |
| Repository | `repository.{entity}.{operation}` | `repository.tenant.get_by_id`, `repository.agent.list` |
| External Call | `external.{service}.{operation}` | `external.payment.process`, `external.auth.validate` |
| Queue Consumer | `consumer.{queue}.{operation}` | `consumer.balance_create.process` |

---

### Span Naming Conventions

| Layer | Pattern | Examples |
|-------|---------|----------|
| HTTP Handler | `handler.{resource}.{action}` | `handler.tenant.create`, `handler.agent.list` |
| Service | `service.{domain}.{operation}` | `service.tenant.create`, `service.agent.register` |
| Repository | `repository.{entity}.{operation}` | `repository.tenant.get_by_id`, `repository.agent.list` |
| External Call | `external.{service}.{operation}` | `external.payment.process`, `external.auth.validate` |
| Queue Consumer | `consumer.{queue}.{operation}` | `consumer.balance_create.process` |

---

### Distributed Tracing: Outgoing Calls (MANDATORY for service-to-service)

When making outgoing calls to other services, **MUST** inject trace context:

```go
// HTTP Client - Inject traceparent/tracestate headers
req, _ := http.NewRequestWithContext(ctx, "POST", url, body)
cotel.InjectHTTPContext(&req.Header, ctx)
resp, err := client.Do(req)

// gRPC Client - Inject into outgoing metadata
ctx = cotel.InjectGRPCContext(ctx)
resp, err := grpcClient.SomeMethod(ctx, req)

// Queue/Message Publisher - Inject into message headers
headers := cotel.PrepareQueueHeaders(ctx, map[string]any{
    "content-type": "application/json",
})
// Use headers when publishing to RabbitMQ/Kafka
```

**Why this matters:**
- Without injection, downstream services create new root traces
- Trace chain breaks, making debugging cross-service issues impossible
- Correlation IDs are lost across service boundaries

---

### Instrumentation Anti-Patterns (FORBIDDEN)

| Anti-Pattern | Problem | Correct Pattern |
|--------------|---------|-----------------|
| `import "go.opentelemetry.io/otel"` | Direct OTel usage bypasses lib-commons wrappers | Use dependency-injected `trace.Core three` from `cotel` |
| `import "go.opentelemetry.io/otel/trace"` | Direct tracer access without lib-commons | Use `cotel` package from lib-commons |
| `otel.Core three("name")` in service code | Scattered tracer creation, no single tracerName | Use `telemetry.StartSpan()` from shared wrapper package |
| `trace.SpanFromContext(ctx)` in service code | Raw OTel API, bypasses wrapper | Use `telemetry.SpanFromContext(ctx)` from shared wrapper |
| Custom error handler | Inconsistent error format across services | Use `chttp.HandleFiberError` in fiber.Config |
| Manual pagination logic | Reinvents cursor/offset pagination | Use `chttp.Pagination`, `chttp.CursorPagination` |
| Custom logging middleware | Inconsistent request logging | Use chttp OTel middleware |
| Manual telemetry middleware | Missing trace context injection | Use `chttp` OTel middleware |
| `log.Printf("[Service] msg")` | No trace correlation, no structured logging | `s.logger.Log(ctx, clog.LevelInfo, "msg")` |
| No span in service method | Operation not traceable | Always create child span |
| `return err` without span handling | Error not attributed to trace | Call `cotel.HandleSpanError` or `cotel.HandleSpanBusinessErrorEvent` |
| Hardcoded trace IDs | Breaks distributed tracing | Use context propagation |
| Missing `defer span.End()` | Span never closes, memory leak | Always defer immediately after Start |
| Using `_` to ignore tracer | No tracing capability | Use dependency-injected tracer |
| Calling downstream without ctx | Trace chain breaks | Pass ctx to all downstream calls |
| Not injecting trace context for outgoing HTTP/gRPC | Remote traces disconnected | Use `cotel.InjectHTTPContext` / `cotel.InjectGRPCContext` |
| `go func() { ... }()` | No panic recovery, no observability | Use `cruntime.SafeGoWithContextAndComponent` |
| `logger.Infof("msg: %s", val)` | v2 format-based logging | Use `s.logger.Log(ctx, level, "msg", clog.String(...))` |
| `libCommons.SetConfigFromEnvVars(&cfg)` | v2 config loading, removed in v5 | Use `libCommons.InitLocalEnvConfig()` + `env.Parse()` |
| `libOpentelemetry.InitializeTelemetry()` | v2 telemetry init, panics on error | Use `cotel.NewTelemetry()` + `tl.ApplyGlobals()` |
| `libZap.InitializeLogger()` | v2 logger init, no config options | Use `czap.New(czap.Config{...})` |
| `libCommons.NewTrackingFromContext(ctx)` | v2 context tracking, removed in v5 | Use dependency-injected logger |
| `libServer.StartWithGracefulShutdown()` | v2 lifecycle, removed in v5 | Use `Service.Run(ctx)` + `Service.Shutdown(ctx)` |
| `libCommons.NewLauncher(...)` | v2 app launcher, removed in v5 | Use `signal.NotifyContext` + `cruntime.SafeGoWithContextAndComponent` |

> **⛔ CRITICAL:** Direct imports of `go.opentelemetry.io/otel`, `go.opentelemetry.io/otel/trace`, `go.opentelemetry.io/otel/attribute`, or `go.opentelemetry.io/otel/codes` are **FORBIDDEN** in application code. All telemetry MUST go through lib-commons wrappers (`cotel`). The only exception is if lib-commons doesn't provide a required OTel feature - in that case, open an issue to add it to lib-commons.

> **⛔ CRITICAL:** Raw goroutines (`go func() { ... }()`) are **FORBIDDEN** in production code. All goroutines MUST use `cruntime.SafeGoWithContextAndComponent` for panic recovery and observability.

> **⛔ CRITICAL:** Direct Fiber response methods (`c.JSON()`, `c.Status().JSON()`, `c.SendString()`) are **FORBIDDEN**. All HTTP responses MUST use `chttp` wrappers (`chttp.OK()`, `chttp.Created()`, `chttp.WithError()`, etc.) to ensure consistent response format across all Lerian services.

### 1. Bootstrap Initialization

```go
// bootstrap/config.go
func InitServersWithOptions(opts ...Option) (*Service, error) {
    libCommons.InitLocalEnvConfig()

    cfg := &Config{}
    if err := env.Parse(cfg); err != nil {
        return nil, fmt.Errorf("parse config: %w", err)
    }

    // Initialize logger FIRST (czap for bootstrap only)
    logger, err := czap.New(czap.Config{
        Level:       cfg.App.LogLevel,
        Development: cfg.App.EnvName != "production",
    })
    if err != nil {
        return nil, fmt.Errorf("init logger: %w", err)
    }

    // Initialize telemetry with config
    tl, err := cotel.NewTelemetry(cotel.TelemetryConfig{
        ServiceName:    cfg.OTel.ServiceName,
        ServiceVersion: cfg.OTel.ServiceVersion,
        DeploymentEnv:  cfg.OTel.DeploymentEnv,
        ExporterEndpoint: cfg.OTel.ExporterEndpoint,
        InsecureExporter: cfg.App.EnvName != "production",
    })
    if err != nil {
        return nil, fmt.Errorf("init telemetry: %w", err)
    }
    if err = tl.ApplyGlobals(); err != nil {
        return nil, fmt.Errorf("apply telemetry globals: %w", err)
    }

    // Pass telemetry to router...
}
```

### 2. Router Middleware Setup

```go
// adapters/http/in/routes.go
import (
    clog "github.com/LerianStudio/lib-commons/v5/commons/log"
    chttp "github.com/LerianStudio/lib-commons/v5/commons/net/http"
    cotel "github.com/LerianStudio/lib-commons/v5/commons/opentelemetry"
    "github.com/gofiber/fiber/v2"
    "github.com/gofiber/fiber/v2/middleware/cors"
    "github.com/gofiber/fiber/v2/middleware/recover"
    "github.com/gofiber/fiber/v2/middleware/requestid"
)

func NewRouter(lg clog.Logger, tl *cotel.Telemetry, ...) *fiber.App {
    f := fiber.New(fiber.Config{
        DisableStartupMessage: true,
        ErrorHandler: func(ctx *fiber.Ctx, err error) error {
            return chttp.HandleFiberError(ctx, err)
        },
    })

    // Middleware setup - ORDER MATTERS (v5 chain)
    f.Use(recover.New())                           // 1. Panic recovery
    f.Use(requestid.New())                         // 2. Request ID
    // f.Use(securityHeaders())                    // 3. Security headers (if applicable)
    // f.Use(rateLimiting())                       // 4. Rate limiting (if applicable)
    f.Use(cors.New())                              // 5. CORS
    // f.Use(sandbox())                            // 6. Sandbox mode (if applicable)
    tm := chttp.NewTelemetryMiddleware(tl)
    f.Use(tm.WithTelemetry(tl, "/health"))         // 7. OpenTelemetry (creates root span)
    // f.Use(tenantMiddleware())                   // 8. Tenant resolution (if multi-tenant)
    // f.Use(orgValidation())                      // 9. Organization validation (if applicable)
    // f.Use(licenseMiddleware())                  // 10. License check (if applicable)

    // ... define routes ...

    // Health and version (no auth required)
    f.Get("/health", chttp.Ping)
    f.Get("/version", chttp.Version)

    return f
}
```

### HTTP Metrics (via chttp OTel Middleware)

The `chttp` OTel middleware from lib-commons v5 provides HTTP metrics collection alongside tracing. It uses standard OpenTelemetry semantic conventions.

**Metrics Collected:**

| Metric | Type | Description |
|--------|------|-------------|
| `http.server.duration` | Histogram | Request duration in milliseconds |
| `http.server.request.size` | Histogram | Request body size in bytes |
| `http.server.response.size` | Histogram | Response body size in bytes |
| `http.server.active_requests` | Gauge | Currently processing requests |

**Why lib-commons middleware over custom middleware:**
- Standard OpenTelemetry semantic conventions
- Automatic trace context propagation
- Consistent with lib-commons patterns
- Compatible with any OpenTelemetry backend (Jaeger, Zipkin, Grafana, etc.)

### 3. Using Logger & Core three (Any Layer)

```go
// any file in any layer (handler, service, repository)
// Logger is dependency-injected; tracer via global wrapper
type Service struct {
    logger clog.Logger
    repo   Repository
}

func (s *Service) ProcessEntity(ctx context.Context, id string) error {
    // Logger is a struct field (dependency-injected)
    // Core three via global wrapper

    // Create child span for this operation
    ctx, span := telemetry.StartSpan(ctx, "service.process_entity")
    defer span.End()

    // Structured logging with typed fields
    s.logger.Log(ctx, clog.LevelInfo, "Processing entity",
        clog.String("id", id))

    // Pass ctx to downstream calls - trace propagates automatically
    return s.repo.Update(ctx, id)
}
```

### 4. Error Handling with Spans

```go
// For technical errors (unexpected failures)
if err != nil {
    cotel.HandleSpanError(&span, "Failed to connect database", err)
    s.logger.Log(ctx, clog.LevelError, "Database error",
        clog.Err(err))
    return nil, err
}

// For business errors (expected validation failures)
if err != nil {
    cotel.HandleSpanBusinessErrorEvent(&span, "Validation failed", err)
    s.logger.Log(ctx, clog.LevelWarn, "Validation error",
        clog.Err(err))
    return nil, err
}
```

### 5. Server Lifecycle with Graceful Shutdown

```go
// bootstrap/service.go
// v5 uses signal.NotifyContext in main.go and Service.Run(ctx)/Shutdown(ctx)
// See the Bootstrap section for complete reference implementations.
func (svc *Service) Run(ctx context.Context) {
    cruntime.SafeGoWithContextAndComponent(
        ctx, svc.logger, "bootstrap", "http-server",
        cruntime.CrashProcess,
        func(goCtx context.Context) {
            if err := svc.app.Listen(svc.serverAddress); err != nil {
                svc.logger.Log(goCtx, clog.LevelError, "HTTP server failed",
                    clog.Err(err))
            }
        },
    )
}

func (svc *Service) Shutdown(ctx context.Context) {
    _ = svc.app.ShutdownWithContext(ctx)
    _ = svc.telemetry.Shutdown(ctx)
    _ = svc.logger.Sync(ctx)
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

---

