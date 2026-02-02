# Go Standards - Core Foundation

> **Module:** core.md | **Sections:** §1-4 | **Parent:** [index.md](index.md)

This module covers the foundational requirements for all Go projects.

---

## Version

- **Minimum**: Go 1.24
- **Recommended**: Latest stable release

---

## Core Dependency: lib-commons (MANDATORY)

All Lerian Studio Go projects **MUST** use `lib-commons/v2` as the foundation library. This ensures consistency across all services.

### Required Import (lib-commons v2)

```go
import (
    libCommons "github.com/LerianStudio/lib-commons/v2/commons"
    libZap "github.com/LerianStudio/lib-commons/v2/commons/zap"           // Logger initialization (config/bootstrap only)
    libLog "github.com/LerianStudio/lib-commons/v2/commons/log"           // Logger interface (services, routes, consumers)
    libOpentelemetry "github.com/LerianStudio/lib-commons/v2/commons/opentelemetry"
    libServer "github.com/LerianStudio/lib-commons/v2/commons/server"
    libHTTP "github.com/LerianStudio/lib-commons/v2/commons/net/http"
    libPostgres "github.com/LerianStudio/lib-commons/v2/commons/postgres"
    libMongo "github.com/LerianStudio/lib-commons/v2/commons/mongo"
    libRedis "github.com/LerianStudio/lib-commons/v2/commons/redis"
)
```

> **Note:** v2 uses `lib` prefix aliases (e.g., `libCommons`, `libZap`, `libLog`) to distinguish lib-commons packages from standard library and other imports.

### What lib-commons Provides

| Package | Purpose | Where Used |
|---------|---------|------------|
| `commons` | Core utilities, config loading, tracking context | Everywhere |
| `commons/zap` | Logger initialization/configuration | **Config/bootstrap files only** |
| `commons/log` | Logger interface (`log.Logger`) for logging operations | Services, routes, consumers, handlers |
| `commons/postgres` | PostgreSQL connection management, pagination | Bootstrap, repositories |
| `commons/mongo` | MongoDB connection management | Bootstrap, repositories |
| `commons/redis` | Redis connection management | Bootstrap, repositories |
| `commons/opentelemetry` | OpenTelemetry initialization and helpers | Bootstrap, middleware |
| `commons/net/http` | HTTP utilities, telemetry middleware, pagination | Routes, handlers |
| `commons/server` | Server lifecycle with graceful shutdown | Bootstrap |

---

## Frameworks & Libraries

### Required Versions (Minimum)

| Library | Minimum Version | Purpose |
|---------|-----------------|---------|
| `lib-commons` | v2.0.0 | Core infrastructure |
| `fiber/v2` | v2.52.0 | HTTP framework |
| `pgx/v5` | v5.7.0 | PostgreSQL driver |
| `go.opentelemetry.io/otel` | v1.38.0 | Telemetry |
| `zap` | v1.27.0 | Logging implementation (internal to lib-commons) |
| `testify` | v1.10.0 | Testing |
| `gomock` | v0.5.0 | Mock generation |
| `mongo-driver` | v1.17.0 | MongoDB driver |
| `go-redis/v9` | v9.7.0 | Redis client |
| `validator/v10` | v10.26.0 | Input validation |

### HTTP Framework

| Library | Use Case |
|---------|----------|
| **Fiber v2** | **Primary choice** - High-performance APIs |
| gRPC-Go | Service-to-service communication |

### Database

| Library | Use Case |
|---------|----------|
| **pgx/v5** | PostgreSQL (recommended) |
| sqlc | Type-safe SQL queries |
| GORM | ORM (when needed) |
| **go-redis/v9** | Redis client |
| **mongo-go-driver** | MongoDB |

### Testing

| Library | Use Case |
|---------|----------|
| testify | Assertions |
| GoMock | Interface mocking (MANDATORY for all mocks) |
| SQLMock | Database mocking |
| testcontainers-go | Integration tests |

---

## Configuration

All services **MUST** use `libCommons.SetConfigFromEnvVars` for configuration loading.

### 1. Define Configuration Struct

```go
// bootstrap/config.go
package bootstrap

const ApplicationName = "your-service-name"

// Config is the top level configuration struct for the entire application.
type Config struct {
    // Application
    EnvName       string `env:"ENV_NAME"`
    LogLevel      string `env:"LOG_LEVEL"`
    ServerAddress string `env:"SERVER_ADDRESS"`

    // Database - Primary
    PrimaryDBHost     string `env:"DB_HOST"`
    PrimaryDBUser     string `env:"DB_USER"`
    PrimaryDBPassword string `env:"DB_PASSWORD"`
    PrimaryDBName     string `env:"DB_NAME"`
    PrimaryDBPort     string `env:"DB_PORT"`
    PrimaryDBSSLMode  string `env:"DB_SSLMODE"`

    // Database - Replica (for read scaling)
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
    MongoDBHost       string `env:"MONGO_HOST"`
    MongoDBName       string `env:"MONGO_NAME"`
    MongoDBUser       string `env:"MONGO_USER"`
    MongoDBPassword   string `env:"MONGO_PASSWORD"`
    MongoDBPort       string `env:"MONGO_PORT"`
    MongoDBParameters string `env:"MONGO_PARAMETERS"`
    MaxPoolSize       int    `env:"MONGO_MAX_POOL_SIZE"`

    // Redis
    RedisHost     string `env:"REDIS_HOST"`
    RedisPassword string `env:"REDIS_PASSWORD"`
    RedisDB       int    `env:"REDIS_DB"`
    RedisPoolSize int    `env:"REDIS_POOL_SIZE"`

    // OpenTelemetry
    OtelServiceName         string `env:"OTEL_RESOURCE_SERVICE_NAME"`
    OtelLibraryName         string `env:"OTEL_LIBRARY_NAME"`
    OtelServiceVersion      string `env:"OTEL_RESOURCE_SERVICE_VERSION"`
    OtelDeploymentEnv       string `env:"OTEL_RESOURCE_DEPLOYMENT_ENVIRONMENT"`
    OtelColExporterEndpoint string `env:"OTEL_EXPORTER_OTLP_ENDPOINT"`
    EnableTelemetry         bool   `env:"ENABLE_TELEMETRY"`

    // Auth
    AuthEnabled bool   `env:"PLUGIN_AUTH_ENABLED"`
    AuthHost    string `env:"PLUGIN_AUTH_HOST"`

    // External Services (gRPC)
    ExternalServiceAddress string `env:"EXTERNAL_SERVICE_GRPC_ADDRESS"`
    ExternalServicePort    string `env:"EXTERNAL_SERVICE_GRPC_PORT"`
}
```

### 2. Load Configuration

```go
// bootstrap/config.go
func InitServers() *Service {
    cfg := &Config{}

    // Load all environment variables into config struct
    if err := libCommons.SetConfigFromEnvVars(cfg); err != nil {
        panic(err)
    }

    // Validate required fields
    if cfg.PrimaryDBHost == "" || cfg.PrimaryDBName == "" {
        panic("DB_HOST and DB_NAME must be configured")
    }

    // Continue with initialization...
}
```

### Supported Types

| Go Type | Default Value | Example |
|---------|---------------|---------|
| `string` | `""` | `ServerAddress string \`env:"SERVER_ADDRESS"\`` |
| `bool` | `false` | `EnableTelemetry bool \`env:"ENABLE_TELEMETRY"\`` |
| `int`, `int8`, `int16`, `int32`, `int64` | `0` | `MaxPoolSize int \`env:"MONGO_MAX_POOL_SIZE"\`` |

### Environment Variable Naming Convention

| Category | Prefix | Example |
|----------|--------|---------|
| Application | None | `ENV_NAME`, `LOG_LEVEL`, `SERVER_ADDRESS` |
| PostgreSQL | `DB_` | `DB_HOST`, `DB_USER`, `DB_PASSWORD` |
| PostgreSQL Replica | `DB_REPLICA_` | `DB_REPLICA_HOST`, `DB_REPLICA_USER` |
| MongoDB | `MONGO_` | `MONGO_HOST`, `MONGO_NAME` |
| Redis | `REDIS_` | `REDIS_HOST`, `REDIS_PASSWORD` |
| OpenTelemetry | `OTEL_` | `OTEL_RESOURCE_SERVICE_NAME` |
| Auth Plugin | `PLUGIN_AUTH_` | `PLUGIN_AUTH_ENABLED`, `PLUGIN_AUTH_HOST` |
| gRPC Services | `{SERVICE}_GRPC_` | `TRANSACTION_GRPC_ADDRESS` |

### What not to Do

```go
// FORBIDDEN: Manual os.Getenv calls scattered across code
host := os.Getenv("DB_HOST")  // DON'T do this

// FORBIDDEN: Configuration outside bootstrap
func NewService() *Service {
    dbHost := os.Getenv("DB_HOST")  // DON'T do this
}

// CORRECT: All configuration in Config struct, loaded once in bootstrap
type Config struct {
    PrimaryDBHost string `env:"DB_HOST"`  // Centralized
}

// Load with: libCommons.SetConfigFromEnvVars(&cfg)
```
