# Go Standards - Bootstrap & Observability

> **Module:** bootstrap.md | **Sections:** §5-6 | **Parent:** [index.md](index.md)

This module covers application initialization and observability.

---

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
│  MIDDLEWARE: f.Use(tlMid.WithTelemetry(tl)) - CREATES ROOT SPAN             │
│                                                                             │
│  What WithTelemetry does:                                                   │
│  1. ExtractHTTPContext(c) - extracts traceparent/tracestate from headers    │
│     → Uses otel.GetTextMapPropagator().Extract() for W3C trace context      │
│     → If traceparent exists: creates child span of remote parent            │
│     → If no traceparent: creates new root span                              │
│  2. tracer.Start(ctx, "GET /api/resource") - creates HTTP ROOT SPAN         │
│  3. Sets span attributes: http.method, http.url, http.route, etc.           │
│  4. ContextWithCore three(ctx, tracer) - injects tracer into context            │
│  5. ContextWithMetricFactory(ctx, factory) - injects metrics factory        │
│  6. c.SetUserContext(ctx) - makes enriched context available to handlers    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  HANDLER LAYER (optional child spans - for complex handlers)                │
│                                                                             │
│  logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)             │
│  ctx, span := tracer.Start(ctx, "handler.create_tenant")                    │
│  defer span.End()                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  SERVICE LAYER (MANDATORY child spans for all methods)                      │
│                                                                             │
│  logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)             │
│  ctx, span := tracer.Start(ctx, "service.tenant.create")                    │
│  defer span.End()                                                           │
│                                                                             │
│  // Structured logging (automatically correlated with trace via context)    │
│  logger.Infof("Creating tenant: name=%s", req.Name)                         │
│                                                                             │
│  // Business errors → AddEvent (span status stays OK)                       │
│  libOpentelemetry.HandleSpanBusinessErrorEvent(&span, "Validation", err)    │
│                                                                             │
│  // Technical errors → SetStatus ERROR + RecordError                        │
│  libOpentelemetry.HandleSpanError(&span, "DB connection failed", err)       │
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
│  libOpentelemetry.InjectHTTPContext(&req.Header, ctx)                       │
│                                                                             │
│  // gRPC Client: Inject into outgoing metadata                              │
│  ctx = libOpentelemetry.InjectGRPCContext(ctx)                              │
│                                                                             │
│  // Queue/Message: Inject into message headers for async trace continuation │
│  headers := libOpentelemetry.PrepareQueueHeaders(ctx, baseHeaders)          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Complete Telemetry Flow (Bootstrap to Shutdown)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. BOOTSTRAP (config.go)                                        │
│    telemetry := libOpentelemetry.InitializeTelemetry(&config)   │
│    → Creates OpenTelemetry provider once at startup             │
│    → Sets global TextMapPropagator for W3C TraceContext         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. ROUTER (routes.go)                                           │
│    tlMid := libHTTP.NewTelemetryMiddleware(tl)                  │
│    f.Use(tlMid.WithTelemetry(tl))      ← Creates root span      │
│    ...routes...                                                  │
│    f.Use(tlMid.EndTracingSpans)        ← Closes root spans      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. any LAYER (handlers, services, repositories)                 │
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

---

### Service Method Instrumentation Checklist (MANDATORY)

**Every service method MUST implement these steps:**

| # | Step | Code Pattern | Purpose |
|---|------|--------------|---------|
| 1 | Extract tracking from context | `logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)` | Get logger/tracer injected by middleware |
| 2 | Create child span | `ctx, span := tracer.Start(ctx, "service.{domain}.{operation}")` | Create traceable operation |
| 3 | Defer span end | `defer span.End()` | Ensure span closes even on panic |
| 4 | Use structured logger | `logger.Infof/Errorf/Warnf(...)` | Logs correlated with trace |
| 5 | Handle business errors | `libOpentelemetry.HandleSpanBusinessErrorEvent(&span, msg, err)` | Expected errors (validation, not found) |
| 6 | Handle technical errors | `libOpentelemetry.HandleSpanError(&span, msg, err)` | Unexpected errors (DB, network) |
| 7 | Pass ctx downstream | All calls receive `ctx` with span | Trace propagation |

---

### Error Handling Classification

| Error Type | Examples | Handler Function | Span Status |
|------------|----------|------------------|-------------|
| **Business Error** | Validation failed, Resource not found, Conflict, Unauthorized | `HandleSpanBusinessErrorEvent` | OK (adds event) |
| **Technical Error** | DB connection failed, Timeout, Network error, Unexpected panic | `HandleSpanError` | ERROR (records error) |

**Why the distinction matters:**
- Business errors are expected and don't indicate system problems
- Technical errors indicate infrastructure issues requiring investigation
- Alerting systems typically trigger on ERROR status spans

---

### Complete Instrumented Service Method Template

```go
func (s *myService) DoSomething(ctx context.Context, req *Request) (*Response, error) {
    // 1. Extract logger and tracer from context (injected by WithTelemetry middleware)
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    // 2. Create child span for this operation
    ctx, span := tracer.Start(ctx, "service.my_service.do_something")
    defer span.End()

    // 3. Structured logging (automatically correlated with trace via context)
    logger.Infof("Processing request: id=%s", req.ID)

    // 4. Input validation - BUSINESS error (expected, span stays OK)
    if req.Name == "" {
        logger.Warn("Validation failed: empty name")
        libOpentelemetry.HandleSpanBusinessErrorEvent(&span, "Validation failed", ErrInvalidInput)
        return nil, fmt.Errorf("%w: name is required", ErrInvalidInput)
    }

    // 5. External call - pass ctx to propagate trace context
    result, err := s.repo.Create(ctx, entity)
    if err != nil {
        // Check if it's a "not found" type error (business) vs DB failure (technical)
        if errors.Is(err, ErrNotFound) {
            logger.Warnf("Entity not found: %s", req.ID)
            libOpentelemetry.HandleSpanBusinessErrorEvent(&span, "Entity not found", err)
            return nil, err
        }

        // TECHNICAL error - unexpected failure, span marked ERROR
        logger.Errorf("Failed to create entity: %v", err)
        libOpentelemetry.HandleSpanError(&span, "Repository create failed", err)
        return nil, fmt.Errorf("failed to create: %w", err)
    }

    logger.Infof("Entity created successfully: id=%s", result.ID)
    return result, nil
}
```

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
libOpentelemetry.InjectHTTPContext(&req.Header, ctx)
resp, err := client.Do(req)

// gRPC Client - Inject into outgoing metadata
ctx = libOpentelemetry.InjectGRPCContext(ctx)
resp, err := grpcClient.SomeMethod(ctx, req)

// Queue/Message Publisher - Inject into message headers
headers := libOpentelemetry.PrepareQueueHeaders(ctx, map[string]any{
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
| `import "go.opentelemetry.io/otel"` | Direct OTel usage bypasses lib-commons wrappers | Use `libCommons.NewTrackingFromContext(ctx)` |
| `import "go.opentelemetry.io/otel/trace"` | Direct tracer access without lib-commons | Use `libOpentelemetry` package from lib-commons |
| `otel.Core three("name")` | Creates standalone tracer, no context integration | Use tracer from `NewTrackingFromContext(ctx)` |
| `trace.SpanFromContext(ctx)` | Raw OTel API, inconsistent with lib-commons | Use `libCommons.NewTrackingFromContext(ctx)` |
| `c.JSON(status, data)` | Direct Fiber response, no standard format | Use `libHTTP.OK(c, data)` or `libHTTP.Created(c, data)` |
| `c.Status(code).JSON(err)` | Inconsistent error responses | Use `libHTTP.WithError(c, err)` |
| Custom error handler | Inconsistent error format across services | Use `libHTTP.HandleFiberError` in fiber.Config |
| Manual pagination logic | Reinvents cursor/offset pagination | Use `libHTTP.Pagination`, `libHTTP.CursorPagination` |
| `c.SendString()` / `c.Send()` | No standard response wrapper | Use `libHTTP.OK()`, `libHTTP.Created()`, `libHTTP.NoContent()` |
| Custom logging middleware | Inconsistent request logging | Use `libHTTP.WithHTTPLogging(libHTTP.WithCustomLogger(lg))` |
| Manual telemetry middleware | Missing trace context injection | Use `libHTTP.NewTelemetryMiddleware(tl).WithTelemetry(tl)` |
| `log.Printf("[Service] msg")` | No trace correlation, no structured logging | `logger.Infof("msg")` from context |
| No span in service method | Operation not traceable | Always create child span |
| `return err` without span handling | Error not attributed to trace | Call `HandleSpanError` or `HandleSpanBusinessErrorEvent` |
| Hardcoded trace IDs | Breaks distributed tracing | Use context propagation |
| Missing `defer span.End()` | Span never closes, memory leak | Always defer immediately after Start |
| Using `_` to ignore tracer | No tracing capability | Extract and use tracer from context |
| Calling downstream without ctx | Trace chain breaks | Pass ctx to all downstream calls |
| Not injecting trace context for outgoing HTTP/gRPC | Remote traces disconnected | Use `InjectHTTPContext` / `InjectGRPCContext` |

> **⛔ CRITICAL:** Direct imports of `go.opentelemetry.io/otel`, `go.opentelemetry.io/otel/trace`, `go.opentelemetry.io/otel/attribute`, or `go.opentelemetry.io/otel/codes` are **FORBIDDEN** in application code. All telemetry MUST go through lib-commons wrappers (`libCommons`, `libOpentelemetry`). The only exception is if lib-commons doesn't provide a required OTel feature - in that case, open an issue to add it to lib-commons.

> **⛔ CRITICAL:** Direct Fiber response methods (`c.JSON()`, `c.Status().JSON()`, `c.SendString()`) are **FORBIDDEN**. All HTTP responses MUST use `libHTTP` wrappers (`libHTTP.OK()`, `libHTTP.Created()`, `libHTTP.WithError()`, etc.) to ensure consistent response format, proper error handling, and telemetry integration across all Lerian services.

### 1. Bootstrap Initialization

```go
// bootstrap/config.go
func InitServers() *Service {
    cfg := &Config{}
    if err := libCommons.SetConfigFromEnvVars(cfg); err != nil {
        panic(err)
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

### 2. Router Middleware Setup

```go
// adapters/http/in/routes.go
import (
    libLog "github.com/LerianStudio/lib-commons/v2/commons/log"
    libHTTP "github.com/LerianStudio/lib-commons/v2/commons/net/http"
    libOpentelemetry "github.com/LerianStudio/lib-commons/v2/commons/opentelemetry"
    "github.com/gofiber/contrib/otelfiber/v2"
    "github.com/gofiber/fiber/v2"
    "github.com/gofiber/fiber/v2/middleware/cors"
    "github.com/gofiber/fiber/v2/middleware/recover"
)

// skipTelemetryPaths returns true for paths that should not be instrumented.
func skipTelemetryPaths(c *fiber.Ctx) bool {
    switch c.Path() {
    case "/health", "/ready", "/metrics":
        return true
    default:
        return false
    }
}

func NewRouter(lg libLog.Logger, tl *libOpentelemetry.Telemetry, ...) *fiber.App {
    f := fiber.New(fiber.Config{
        DisableStartupMessage: true,
        ErrorHandler: func(ctx *fiber.Ctx, err error) error {
            return libHTTP.HandleFiberError(ctx, err)
        },
    })

    // Create telemetry middleware
    tlMid := libHTTP.NewTelemetryMiddleware(tl)

    // Middleware setup - ORDER MATTERS
    f.Use(tlMid.WithTelemetry(tl))                                    // 1. Must be first - injects tracer+logger into context
    f.Use(recover.New())                                              // 2. Panic recovery
    f.Use(cors.New())                                                 // 3. CORS
    f.Use(otelfiber.Middleware(otelfiber.WithNext(skipTelemetryPaths))) // 4. OpenTelemetry metrics
    f.Use(libHTTP.WithHTTPLogging(libHTTP.WithCustomLogger(lg)))      // 5. HTTP logging

    // ... define routes ...

    // Version endpoint
    f.Get("/version", libHTTP.Version)

    // MUST be last middleware - closes root spans
    f.Use(tlMid.EndTracingSpans)

    return f
}
```

### otelfiber Metrics Middleware (MANDATORY)

All Fiber services **MUST** use `otelfiber` for HTTP metrics collection. This provides standard OpenTelemetry metrics without custom implementation.

**Installation:**
```bash
go get github.com/gofiber/contrib/otelfiber/v2
```

**Metrics Collected:**

| Metric | Type | Description |
|--------|------|-------------|
| `http.server.duration` | Histogram | Request duration in milliseconds |
| `http.server.request.size` | Histogram | Request body size in bytes |
| `http.server.response.size` | Histogram | Response body size in bytes |
| `http.server.active_requests` | Gauge | Currently processing requests |

**Configuration Options:**

| Option | Purpose |
|--------|---------|
| `WithNext(func)` | Skip instrumentation for certain paths |
| `WithCore threeProvider(tp)` | Custom tracer provider |
| `WithMeterProvider(mp)` | Custom meter provider |
| `WithSpanNameFormatter(func)` | Custom span naming |

**Why otelfiber over custom middleware:**
- Standard OpenTelemetry semantic conventions
- Automatic trace context propagation
- No custom code to maintain
- Compatible with any OpenTelemetry backend (Jaeger, Zipkin, Grafana, etc.)

### 3. Recovering Logger & Core three (Any Layer)

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

### 4. Error Handling with Spans

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

### 5. Server Lifecycle with Graceful Shutdown

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

---

## Bootstrap

All services **MUST** follow the bootstrap pattern for initialization. The bootstrap package is the single point of application assembly where all dependencies are wired together.

### Directory Structure

```text
/internal
  /bootstrap
    config.go          # Config struct + InitServers() - Main initialization logic
    fiber.server.go    # HTTP server with graceful shutdown (or server.go)
    grpc.server.go     # gRPC server (if needed)
    service.go         # Service struct wrapping servers + Run() method
```

### Reference Implementations

The following sections provide **complete, copy-pasteable** implementations for each bootstrap file. These are extracted from production repositories (midaz, plugin-auth, plugin-fees).

---

### config.go - Complete Reference

This is the main initialization file that wires all dependencies together.

```go
package bootstrap

import (
    "context"
    "fmt"
    "strings"
    "time"

    libCommons "github.com/LerianStudio/lib-commons/v2/commons"
    libMongo "github.com/LerianStudio/lib-commons/v2/commons/mongo"
    libOpentelemetry "github.com/LerianStudio/lib-commons/v2/commons/opentelemetry"
    libPostgres "github.com/LerianStudio/lib-commons/v2/commons/postgres"
    libRedis "github.com/LerianStudio/lib-commons/v2/commons/redis"
    libZap "github.com/LerianStudio/lib-commons/v2/commons/zap"

    // Internal imports
    httpin "github.com/LerianStudio/your-service/internal/adapters/http/in"
    "github.com/LerianStudio/your-service/internal/adapters/postgres/user"
    "github.com/LerianStudio/your-service/internal/services/command"
    "github.com/LerianStudio/your-service/internal/services/query"
)

// ApplicationName identifies this service in logs, traces, and metrics.
const ApplicationName = "your-service"

// Config is the top level configuration struct for the entire application.
// All fields are populated from environment variables via `env:` tags.
type Config struct {
    // Application
    EnvName       string `env:"ENV_NAME"`
    ServerAddress string `env:"SERVER_ADDRESS"`
    LogLevel      string `env:"LOG_LEVEL"`

    // Database - Primary
    PrimaryDBHost      string `env:"DB_HOST"`
    PrimaryDBUser      string `env:"DB_USER"`
    PrimaryDBPassword  string `env:"DB_PASSWORD"`
    PrimaryDBName      string `env:"DB_NAME"`
    PrimaryDBPort      string `env:"DB_PORT"`
    PrimaryDBSSLMode   string `env:"DB_SSLMODE"`

    // Database - Replica (optional, for read scaling)
    ReplicaDBHost     string `env:"DB_REPLICA_HOST"`
    ReplicaDBUser     string `env:"DB_REPLICA_USER"`
    ReplicaDBPassword string `env:"DB_REPLICA_PASSWORD"`
    ReplicaDBName     string `env:"DB_REPLICA_NAME"`
    ReplicaDBPort     string `env:"DB_REPLICA_PORT"`
    ReplicaDBSSLMode  string `env:"DB_REPLICA_SSLMODE"`

    // Database - Connection Pool
    MaxOpenConnections int `env:"DB_MAX_OPEN_CONNS"`
    MaxIdleConnections int `env:"DB_MAX_IDLE_CONNS"`

    // MongoDB (if needed)
    MongoURI          string `env:"MONGO_URI"`
    MongoDBHost       string `env:"MONGO_HOST"`
    MongoDBName       string `env:"MONGO_NAME"`
    MongoDBUser       string `env:"MONGO_USER"`
    MongoDBPassword   string `env:"MONGO_PASSWORD"`
    MongoDBPort       string `env:"MONGO_PORT"`
    MongoDBParameters string `env:"MONGO_PARAMETERS"`
    MaxPoolSize       int    `env:"MONGO_MAX_POOL_SIZE"`

    // Redis (if needed)
    RedisHost                    string `env:"REDIS_HOST"`
    RedisMasterName              string `env:"REDIS_MASTER_NAME" default:""`
    RedisPassword                string `env:"REDIS_PASSWORD"`
    RedisDB                      int    `env:"REDIS_DB" default:"0"`
    RedisProtocol                int    `env:"REDIS_PROTOCOL" default:"3"`
    RedisTLS                     bool   `env:"REDIS_TLS" default:"false"`
    RedisCACert                  string `env:"REDIS_CA_CERT"`
    RedisUseGCPIAM               bool   `env:"REDIS_USE_GCP_IAM" default:"false"`
    RedisServiceAccount          string `env:"REDIS_SERVICE_ACCOUNT" default:""`
    GoogleApplicationCredentials string `env:"GOOGLE_APPLICATION_CREDENTIALS" default:""`
    RedisTokenLifeTime           int    `env:"REDIS_TOKEN_LIFETIME" default:"60"`
    RedisTokenRefreshDuration    int    `env:"REDIS_TOKEN_REFRESH_DURATION" default:"45"`

    // OpenTelemetry
    OtelServiceName         string `env:"OTEL_RESOURCE_SERVICE_NAME"`
    OtelLibraryName         string `env:"OTEL_LIBRARY_NAME"`
    OtelServiceVersion      string `env:"OTEL_RESOURCE_SERVICE_VERSION"`
    OtelDeploymentEnv       string `env:"OTEL_RESOURCE_DEPLOYMENT_ENVIRONMENT"`
    OtelColExporterEndpoint string `env:"OTEL_EXPORTER_OTLP_ENDPOINT"`
    EnableTelemetry         bool   `env:"ENABLE_TELEMETRY"`

    // Auth (if using plugin-auth)
    AuthEnabled bool   `env:"PLUGIN_AUTH_ENABLED"`
    AuthHost    string `env:"PLUGIN_AUTH_HOST"`
}

// InitServers initializes all application components and returns a Service ready to run.
// This is the single point of dependency injection for the entire application.
func InitServers() *Service {
    // 1. LOAD CONFIGURATION
    // All environment variables are loaded into the Config struct
    cfg := &Config{}
    if err := libCommons.SetConfigFromEnvVars(cfg); err != nil {
        panic(err)
    }

    // 2. INITIALIZE LOGGER
    // Must be first after config - all subsequent components need logging
    logger := libZap.InitializeLogger()

    // 3. INITIALIZE TELEMETRY
    // OpenTelemetry provider for distributed tracing
    telemetry := libOpentelemetry.InitializeTelemetry(&libOpentelemetry.TelemetryConfig{
        LibraryName:               cfg.OtelLibraryName,
        ServiceName:               cfg.OtelServiceName,
        ServiceVersion:            cfg.OtelServiceVersion,
        DeploymentEnv:             cfg.OtelDeploymentEnv,
        CollectorExporterEndpoint: cfg.OtelColExporterEndpoint,
        EnableTelemetry:           cfg.EnableTelemetry,
        Logger:                    logger,
    })

    // 4. INITIALIZE DATABASE CONNECTIONS
    // PostgreSQL connection with primary/replica support
    postgreSourcePrimary := fmt.Sprintf("host=%s user=%s password=%s dbname=%s port=%s sslmode=%s",
        cfg.PrimaryDBHost, cfg.PrimaryDBUser, cfg.PrimaryDBPassword,
        cfg.PrimaryDBName, cfg.PrimaryDBPort, cfg.PrimaryDBSSLMode)

    postgreSourceReplica := postgreSourcePrimary
    if cfg.ReplicaDBHost != "" {
        postgreSourceReplica = fmt.Sprintf("host=%s user=%s password=%s dbname=%s port=%s sslmode=%s",
            cfg.ReplicaDBHost, cfg.ReplicaDBUser, cfg.ReplicaDBPassword,
            cfg.ReplicaDBName, cfg.ReplicaDBPort, cfg.ReplicaDBSSLMode)
    }

    postgresConnection := &libPostgres.PostgresConnection{
        ConnectionStringPrimary: postgreSourcePrimary,
        ConnectionStringReplica: postgreSourceReplica,
        PrimaryDBName:           cfg.PrimaryDBName,
        ReplicaDBName:           cfg.ReplicaDBName,
        Component:               ApplicationName,
        Logger:                  logger,
        MaxOpenConnections:      cfg.MaxOpenConnections,
        MaxIdleConnections:      cfg.MaxIdleConnections,
    }

    // MongoDB connection (optional - include only if service uses MongoDB)
    mongoSource := fmt.Sprintf("%s://%s:%s@%s:%s/",
        cfg.MongoURI, cfg.MongoDBUser, cfg.MongoDBPassword, cfg.MongoDBHost, cfg.MongoDBPort)
    if cfg.MaxPoolSize <= 0 {
        cfg.MaxPoolSize = 100
    }
    if cfg.MongoDBParameters != "" {
        mongoSource += "?" + cfg.MongoDBParameters
    }
    mongoConnection := &libMongo.MongoConnection{
        ConnectionStringSource: mongoSource,
        Database:               cfg.MongoDBName,
        Logger:                 logger,
        MaxPoolSize:            uint64(cfg.MaxPoolSize),
    }

    // Redis connection (optional - include only if service uses Redis)
    redisConnection := &libRedis.RedisConnection{
        Address:                      strings.Split(cfg.RedisHost, ","),
        Password:                     cfg.RedisPassword,
        DB:                           cfg.RedisDB,
        Protocol:                     cfg.RedisProtocol,
        MasterName:                   cfg.RedisMasterName,
        UseTLS:                       cfg.RedisTLS,
        CACert:                       cfg.RedisCACert,
        UseGCPIAMAuth:                cfg.RedisUseGCPIAM,
        ServiceAccount:               cfg.RedisServiceAccount,
        GoogleApplicationCredentials: cfg.GoogleApplicationCredentials,
        TokenLifeTime:                time.Duration(cfg.RedisTokenLifeTime) * time.Minute,
        RefreshDuration:              time.Duration(cfg.RedisTokenRefreshDuration) * time.Minute,
        Logger:                       logger,
    }

    // 5. INITIALIZE REPOSITORIES (Adapters)
    // Each repository uses the appropriate database connection
    userPostgreSQLRepository := user.NewUserPostgreSQLRepository(postgresConnection)
    // metadataMongoDBRepository := mongodb.NewMetadataMongoDBRepository(mongoConnection)
    // cacheRedisRepository := redis.NewCacheRepository(redisConnection)

    // 6. INITIALIZE USE CASES (Services/Business Logic)
    // Command use case for write operations
    commandUseCase := &command.UseCase{
        UserRepo: userPostgreSQLRepository,
        // MetadataRepo: metadataMongoDBRepository,
        // CacheRepo: cacheRedisRepository,
    }
    // Query use case for read operations
    queryUseCase := &query.UseCase{
        UserRepo: userPostgreSQLRepository,
        // MetadataRepo: metadataMongoDBRepository,
    }

    // 7. INITIALIZE HANDLERS
    // HTTP handlers receive use cases for request processing
    userHandler := &httpin.UserHandler{
        Command: commandUseCase,
        Query:   queryUseCase,
    }

    // 8. CREATE ROUTER WITH MIDDLEWARE
    // NewRouter sets up Fiber with telemetry middleware, logging, and routes
    httpApp := httpin.NewRouter(logger, telemetry, userHandler)

    // 9. CREATE SERVER
    // Server wraps the Fiber app with graceful shutdown support
    serverAPI := NewServer(cfg, httpApp, logger, telemetry)

    // 10. RETURN SERVICE
    // Service orchestrates server lifecycle
    return &Service{
        Server: serverAPI,
        Logger: logger,
    }
}
```

**Key Points:**
- `InitServers()` is the only place where dependencies are wired together
- Order matters: config → logger → telemetry → databases → repositories → services → handlers → router → server
- All database connections use lib-commons packages
- The function returns a `*Service` that is ready to run

---

### fiber.server.go - Complete Reference

This file defines the HTTP server with graceful shutdown support.

```go
package bootstrap

import (
    libCommons "github.com/LerianStudio/lib-commons/v2/commons"
    libLog "github.com/LerianStudio/lib-commons/v2/commons/log"
    libOpentelemetry "github.com/LerianStudio/lib-commons/v2/commons/opentelemetry"
    libCommonsServer "github.com/LerianStudio/lib-commons/v2/commons/server"
    "github.com/gofiber/fiber/v2"
)

// Server represents the HTTP server for the service.
type Server struct {
    app           *fiber.App
    serverAddress string
    logger        libLog.Logger
    telemetry     libOpentelemetry.Telemetry
}

// ServerAddress returns the server's listen address.
func (s *Server) ServerAddress() string {
    return s.serverAddress
}

// NewServer creates a new Server instance.
func NewServer(cfg *Config, app *fiber.App, logger libLog.Logger, telemetry *libOpentelemetry.Telemetry) *Server {
    return &Server{
        app:           app,
        serverAddress: cfg.ServerAddress,
        logger:        logger,
        telemetry:     *telemetry,
    }
}

// Run starts the HTTP server with graceful shutdown.
// This method is called by the Launcher and handles:
// - Signal trapping (SIGINT, SIGTERM)
// - Telemetry flush on shutdown
// - Connection draining
func (s *Server) Run(l *libCommons.Launcher) error {
    libCommonsServer.NewServerManager(nil, &s.telemetry, s.logger).
        WithHTTPServer(s.app, s.serverAddress).
        StartWithGracefulShutdown()

    return nil
}
```

**Key Points:**
- `Run(*libCommons.Launcher)` signature is required for the Launcher
- `libCommonsServer.NewServerManager` handles all graceful shutdown logic
- Telemetry is passed to ensure spans are flushed before shutdown

---

### service.go - Complete Reference

This file defines the Service struct that orchestrates the application lifecycle.

```go
package bootstrap

import (
    libCommons "github.com/LerianStudio/lib-commons/v2/commons"
    libLog "github.com/LerianStudio/lib-commons/v2/commons/log"
)

// Service is the application glue where we put all top level components to be used.
type Service struct {
    *Server
    libLog.Logger
}

// Run starts the application.
// This is the only necessary code to run an app in main.go
func (app *Service) Run() {
    libCommons.NewLauncher(
        libCommons.WithLogger(app.Logger),
        libCommons.RunApp("Fiber Server", app.Server),
    ).Run()
}
```

**Key Points:**
- Service embeds `*Server` and `libLog.Logger`
- `Run()` uses `libCommons.NewLauncher` to manage application lifecycle
- For multiple servers (HTTP + gRPC + Worker), add multiple `RunApp` calls:

```go
func (app *Service) Run() {
    libCommons.NewLauncher(
        libCommons.WithLogger(app.Logger),
        libCommons.RunApp("HTTP Server", app.HTTPServer),
        libCommons.RunApp("gRPC Server", app.GRPCServer),
        libCommons.RunApp("RabbitMQ Consumer", app.Consumer),
    ).Run()
}
```

---

### main.go - Complete Reference

The main.go file should be minimal, delegating to bootstrap.

```go
package main

import "github.com/LerianStudio/your-service/internal/bootstrap"

func main() {
    bootstrap.InitServers().Run()
}
```

**That's it.** All complexity is encapsulated in bootstrap.

---

