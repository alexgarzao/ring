## Bootstrap

All services **MUST** follow the bootstrap pattern for initialization. The bootstrap package is the single point of application assembly where all dependencies are wired together.

### Directory Structure

```text
/internal
  /bootstrap
    config.go          # Config struct + InitServers() - Main initialization logic
    service.go         # Service lifecycle, DI, Fiber setup
    grpc.server.go     # gRPC server (if needed)
    service.go         # Service struct wrapping servers + Run() method
```

### Reference Implementations

The following sections provide **complete, copy-pasteable** implementations for each bootstrap file. These are extracted from production repositories (plugin-br-bank-transfer-jd).

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

    libCommons "github.com/LerianStudio/lib-commons/v5/commons"
    clog "github.com/LerianStudio/lib-commons/v5/commons/log"
    czap "github.com/LerianStudio/lib-commons/v5/commons/zap"
    cotel "github.com/LerianStudio/lib-commons/v5/commons/opentelemetry"
    cpostgres "github.com/LerianStudio/lib-commons/v5/commons/postgres"
    cmongo "github.com/LerianStudio/lib-commons/v5/commons/mongo"
    credis "github.com/LerianStudio/lib-commons/v5/commons/redis"
    cruntime "github.com/LerianStudio/lib-commons/v5/commons/runtime"

    "github.com/caarlos0/env/v11"

    // Internal imports
    httpin "github.com/LerianStudio/your-service/internal/adapters/http/in"
    "github.com/LerianStudio/your-service/internal/adapters/postgres/user"
    "github.com/LerianStudio/your-service/internal/services/command"
    "github.com/LerianStudio/your-service/internal/services/query"
)

// ApplicationName identifies this service in logs, traces, and metrics.
const ApplicationName = "your-service"

// Config is the top level configuration struct for the entire application.
// v5 uses nested structs with `envPrefix` tags for grouping.
type Config struct {
    App   AppConfig   `envPrefix:""`
    Postgres PostgresConfig `envPrefix:"POSTGRES_"`
    Mongo    MongoConfig    `envPrefix:"MONGO_"`
    Redis    RedisConfig    `envPrefix:"REDIS_"`
    OTel     OTelConfig     `envPrefix:"OTEL_"`
    Auth     AuthConfig     `envPrefix:"PLUGIN_AUTH_"`
}

// (See Configuration section above for nested struct definitions)

// InitServersWithOptions initializes all application components and returns a Service ready to run.
// This is the single point of dependency injection for the entire application.
// v5 returns error instead of panicking.
func InitServersWithOptions(opts ...Option) (*Service, error) {
    // 1. LOAD CONFIGURATION
    // InitLocalEnvConfig loads .env for local dev (no-op in production)
    libCommons.InitLocalEnvConfig()

    cfg := &Config{}
    if err := env.Parse(cfg); err != nil {
        return nil, fmt.Errorf("parse config: %w", err)
    }

    // 2. INITIALIZE LOGGER
    // Must be first after config - all subsequent components need logging
    logger, err := czap.New(czap.Config{
        Level:       cfg.App.LogLevel,
        Development: cfg.App.EnvName != "production",
    })
    if err != nil {
        return nil, fmt.Errorf("init logger: %w", err)
    }

    // 3. INITIALIZE TELEMETRY
    // OpenTelemetry provider for distributed tracing
    tl, err := cotel.NewTelemetry(cotel.TelemetryConfig{
        ServiceName:      cfg.OTel.ServiceName,
        ServiceVersion:   cfg.OTel.ServiceVersion,
        DeploymentEnv:    cfg.OTel.DeploymentEnv,
        ExporterEndpoint: cfg.OTel.ExporterEndpoint,
        InsecureExporter: cfg.App.EnvName != "production",
    })
    if err != nil {
        return nil, fmt.Errorf("init telemetry: %w", err)
    }
    if err = tl.ApplyGlobals(); err != nil {
        return nil, fmt.Errorf("apply telemetry globals: %w", err)
    }

    // 4. INITIALIZE POSTGRESQL CONNECTIONS
    // PostgreSQL connection with primary/replica support
    postgreSourcePrimary := fmt.Sprintf("host=%s user=%s password=%s dbname=%s port=%s sslmode=%s",
        cfg.Postgres.Host, cfg.Postgres.User, cfg.Postgres.Password,
        cfg.Postgres.Name, cfg.Postgres.Port, cfg.Postgres.SSLMode)

    postgreSourceReplica := postgreSourcePrimary
    if cfg.Postgres.ReplicaHost != "" {
        postgreSourceReplica = fmt.Sprintf("host=%s user=%s password=%s dbname=%s port=%s sslmode=%s",
            cfg.Postgres.ReplicaHost, cfg.Postgres.ReplicaUser, cfg.Postgres.ReplicaPassword,
            cfg.Postgres.ReplicaName, cfg.Postgres.ReplicaPort, cfg.Postgres.ReplicaSSLMode)
    }

    postgresConnection := &cpostgres.PostgresConnection{
        ConnectionStringPrimary: postgreSourcePrimary,
        ConnectionStringReplica: postgreSourceReplica,
        PrimaryName:             cfg.Postgres.Name,
        ReplicaName:             cfg.Postgres.ReplicaName,
        Component:               ApplicationName,
        Logger:                  logger,
        MaxOpenConnections:      cfg.Postgres.MaxOpenConns,
        MaxIdleConnections:      cfg.Postgres.MaxIdleConns,
    }

    // MongoDB connection (optional - include only if service uses MongoDB)
    mongoSource := fmt.Sprintf("%s://%s:%s@%s:%s/",
        cfg.Mongo.URI, cfg.Mongo.User, cfg.Mongo.Password, cfg.Mongo.Host, cfg.Mongo.Port)
    if cfg.Mongo.MaxPool <= 0 {
        cfg.Mongo.MaxPool = 100
    }
    if cfg.Mongo.Parameters != "" {
        mongoSource += "?" + cfg.Mongo.Parameters
    }
    mongoConnection := &cmongo.MongoConnection{
        ConnectionStringSource: mongoSource,
        Database:               cfg.Mongo.Name,
        Logger:                 logger,
        MaxPoolSize:            uint64(cfg.Mongo.MaxPool),
    }

    // Redis connection (optional - include only if service uses Redis)
    redisConnection := &credis.RedisConnection{
        Address:                      strings.Split(cfg.Redis.Host, ","),
        Password:                     cfg.Redis.Password,
        DB:                           cfg.Redis.DB,
        Protocol:                     cfg.Redis.Protocol,
        MasterName:                   cfg.Redis.MasterName,
        UseTLS:                       cfg.Redis.TLS,
        CACert:                       cfg.Redis.CACert,
        UseGCPIAMAuth:                cfg.Redis.UseGCPIAM,
        ServiceAccount:               cfg.Redis.ServiceAccount,
        GoogleApplicationCredentials: cfg.Redis.GoogleApplicationCredentials,
        TokenLifeTime:                time.Duration(cfg.Redis.TokenLifeTime) * time.Minute,
        RefreshDuration:              time.Duration(cfg.Redis.TokenRefreshDuration) * time.Minute,
        Logger:                       logger,
    }

    // 5. INITIALIZE REPOSITORIES (Adapters)
    userPostgreSQLRepository := user.NewUserPostgreSQLRepository(postgresConnection)
    // metadataMongoDBRepository := mongodb.NewMetadataMongoDBRepository(mongoConnection)
    // cacheRedisRepository := redis.NewCacheRepository(redisConnection)

    // 6. INITIALIZE USE CASES (Services/Business Logic)
    commandUseCase := &command.UseCase{
        UserRepo: userPostgreSQLRepository,
    }
    queryUseCase := &query.UseCase{
        UserRepo: userPostgreSQLRepository,
    }

    // 7. INITIALIZE HANDLERS
    userHandler := &httpin.UserHandler{
        Command: commandUseCase,
        Query:   queryUseCase,
    }

    // 8. CREATE ROUTER WITH MIDDLEWARE
    httpApp := httpin.NewRouter(logger, tl, userHandler)

    // 9. RETURN SERVICE
    // Service holds all components for lifecycle management
    return &Service{
        app:           httpApp,
        serverAddress: cfg.App.ServerAddress,
        logger:        logger,
        telemetry:     tl,
    }, nil
}
```

**Key Points:**
- `InitServersWithOptions()` returns `(*Service, error)` instead of panicking
- Uses nested config structs with `envPrefix` tags
- Uses `czap.New()` instead of `libZap.InitializeLogger()`
- Uses `cotel.NewTelemetry()` + `tl.ApplyGlobals()` instead of `libOpentelemetry.InitializeTelemetry()`
- Order matters: config → logger → telemetry → databases → repositories → services → handlers → router → service
- All database connections use lib-commons v5 packages

---

### service.go - Complete Reference

In v5, the `Service` struct manages the full lifecycle. There is no separate `Server` struct or `Launcher`.

```go
package bootstrap

import (
    "context"
    "fmt"

    clog "github.com/LerianStudio/lib-commons/v5/commons/log"
    cotel "github.com/LerianStudio/lib-commons/v5/commons/opentelemetry"
    cruntime "github.com/LerianStudio/lib-commons/v5/commons/runtime"
    "github.com/gofiber/fiber/v2"
)

// Service holds all components and manages application lifecycle.
type Service struct {
    app           *fiber.App
    serverAddress string
    logger        clog.Logger
    telemetry     *cotel.Telemetry
}

// Run starts all application components.
// Uses cruntime.SafeGoWithContextAndComponent for safe goroutine management.
func (svc *Service) Run(ctx context.Context) {
    svc.logger.Log(ctx, clog.LevelInfo, "Starting HTTP server",
        clog.String("address", svc.serverAddress))

    cruntime.SafeGoWithContextAndComponent(
        ctx,
        svc.logger,
        "bootstrap",
        "http-server",
        cruntime.CrashProcess,
        func(goCtx context.Context) {
            if err := svc.app.Listen(svc.serverAddress); err != nil {
                svc.logger.Log(goCtx, clog.LevelError, "HTTP server failed",
                    clog.Err(err))
            }
        },
    )
}

// Shutdown gracefully stops all components.
// Called when context is cancelled (SIGINT/SIGTERM).
func (svc *Service) Shutdown(ctx context.Context) {
    svc.logger.Log(ctx, clog.LevelInfo, "Shutting down...")

    if err := svc.app.ShutdownWithContext(ctx); err != nil {
        svc.logger.Log(ctx, clog.LevelError, "HTTP shutdown error",
            clog.Err(err))
    }

    if err := svc.telemetry.Shutdown(ctx); err != nil {
        svc.logger.Log(ctx, clog.LevelError, "Telemetry shutdown error",
            clog.Err(err))
    }

    _ = svc.logger.Sync(ctx)
}
```

**Key Points:**
- No more `libCommons.Launcher` or `libCommonsServer.NewServerManager`
- `Run(ctx)` uses `cruntime.SafeGoWithContextAndComponent` for safe goroutines
- `Shutdown(ctx)` flushes telemetry and syncs logger
- Signal handling is done in `main.go` via `signal.NotifyContext`

---

### Multiple Components (HTTP + gRPC + Worker)

For services with multiple components, start each in its own safe goroutine:

```go
func (svc *Service) Run(ctx context.Context) {
    // HTTP Server
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

    // gRPC Server (if applicable)
    cruntime.SafeGoWithContextAndComponent(
        ctx, svc.logger, "bootstrap", "grpc-server",
        cruntime.CrashProcess,
        func(goCtx context.Context) {
            if err := svc.grpcServer.Serve(svc.grpcListener); err != nil {
                svc.logger.Log(goCtx, clog.LevelError, "gRPC server failed",
                    clog.Err(err))
            }
        },
    )

    // RabbitMQ Consumer (if applicable)
    cruntime.SafeGoWithContextAndComponent(
        ctx, svc.logger, "bootstrap", "rabbitmq-consumer",
        cruntime.CrashProcess,
        func(goCtx context.Context) {
            svc.consumer.RunConsumers(goCtx)
        },
    )
}
```

---

### main.go - Complete Reference

The main.go file uses `os.Exit(run())` pattern with `signal.NotifyContext` for graceful shutdown.

```go
package main

import (
    "context"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/LerianStudio/your-service/internal/bootstrap"
)

const shutdownTimeout = 10 * time.Second

func main() {
    os.Exit(run())
}

func run() int {
    // Create context that cancels on SIGINT/SIGTERM
    ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
    defer stop()

    // Initialize all components (returns error instead of panicking)
    svc, err := bootstrap.InitServersWithOptions()
    if err != nil {
        // Cannot use logger here - it failed to initialize
        os.Stderr.WriteString("failed to initialize: " + err.Error() + "\n")
        return 1
    }

    // Start all components (non-blocking)
    svc.Run(ctx)

    // Wait for signal
    <-ctx.Done()

    // Graceful shutdown with timeout
    shutdownCtx, cancel := context.WithTimeout(context.Background(), shutdownTimeout)
    defer cancel()

    svc.Shutdown(shutdownCtx)

    return 0
}
```

**Key Points:**
- `os.Exit(run())` ensures deferred functions run before exit
- `signal.NotifyContext` replaces manual signal handling
- `InitServersWithOptions()` returns `(*Service, error)` - no panics
- Graceful shutdown with configurable timeout

---

