## Configuration

All services **MUST** use `libCommons.InitLocalEnvConfig()` for configuration loading. v5 uses **nested config structs** that group related settings together.

### 1. Define Configuration Struct (Nested Pattern)

```go
// bootstrap/config.go
package bootstrap

const ApplicationName = "your-service-name"

// Config is the top level configuration struct for the entire application.
// v5 uses nested structs to group related configuration.
type Config struct {
    App   AppConfig   `envPrefix:""`
    Postgres PostgresConfig `envPrefix:"POSTGRES_"`
    Mongo    MongoConfig    `envPrefix:"MONGO_"`
    Redis    RedisConfig    `envPrefix:"REDIS_"`
    OTel     OTelConfig     `envPrefix:"OTEL_"`
    Auth     AuthConfig     `envPrefix:"PLUGIN_AUTH_"`
}

type AppConfig struct {
    EnvName       string `env:"ENV_NAME"`
    LogLevel      string `env:"LOG_LEVEL"`
    ServerAddress string `env:"SERVER_ADDRESS"`
}

type PostgresConfig struct {
    Host            string `env:"HOST"`
    User            string `env:"USER"`
    Password        string `env:"PASSWORD"`
    Name            string `env:"NAME"`
    Port            string `env:"PORT"`
    SSLMode         string `env:"SSLMODE"`
    ReplicaHost     string `env:"REPLICA_HOST"`
    ReplicaUser     string `env:"REPLICA_USER"`
    ReplicaPassword string `env:"REPLICA_PASSWORD"`
    ReplicaName     string `env:"REPLICA_NAME"`
    ReplicaPort     string `env:"REPLICA_PORT"`
    ReplicaSSLMode  string `env:"REPLICA_SSLMODE"`
    MaxOpenConns    int    `env:"MAX_OPEN_CONNS"`
    MaxIdleConns    int    `env:"MAX_IDLE_CONNS"`
}

type MongoConfig struct {
    URI        string `env:"URI"`
    Host       string `env:"HOST"`
    Name       string `env:"NAME"`
    User       string `env:"USER"`
    Password   string `env:"PASSWORD"`
    Port       string `env:"PORT"`
    Parameters string `env:"PARAMETERS"`
    MaxPool    int    `env:"MAX_POOL_SIZE"`
}

type RedisConfig struct {
    Host                        string `env:"HOST"`
    MasterName                  string `env:"MASTER_NAME" envDefault:""`
    Password                    string `env:"PASSWORD"`
    DB                          int    `env:"DB" envDefault:"0"`
    Protocol                    int    `env:"PROTOCOL" envDefault:"3"`
    TLS                         bool   `env:"TLS" envDefault:"false"`
    CACert                      string `env:"CA_CERT"`
    UseGCPIAM                   bool   `env:"USE_GCP_IAM" envDefault:"false"`
    ServiceAccount              string `env:"SERVICE_ACCOUNT" envDefault:""`
    GoogleApplicationCredentials string `env:"GOOGLE_APPLICATION_CREDENTIALS" envDefault:""`
    TokenLifeTime               int    `env:"TOKEN_LIFETIME" envDefault:"60"`
    TokenRefreshDuration        int    `env:"TOKEN_REFRESH_DURATION" envDefault:"45"`
}

type OTelConfig struct {
    ServiceName      string `env:"RESOURCE_SERVICE_NAME"`
    LibraryName      string `env:"LIBRARY_NAME"`
    ServiceVersion   string `env:"RESOURCE_SERVICE_VERSION"`
    DeploymentEnv    string `env:"RESOURCE_DEPLOYMENT_ENVIRONMENT"`
    ExporterEndpoint string `env:"EXPORTER_OTLP_ENDPOINT"`
    EnableTelemetry  bool   `env:"ENABLE_TELEMETRY"`
}

type AuthConfig struct {
    Enabled bool   `env:"ENABLED"`
    Address string `env:"ADDRESS"`
}
```

### 2. Load Configuration

```go
// bootstrap/config.go
func InitServersWithOptions(opts ...Option) (*Service, error) {
    // Load .env file for local development (no-op in production)
    libCommons.InitLocalEnvConfig()

    cfg := &Config{}
    if err := env.Parse(cfg); err != nil {
        return nil, fmt.Errorf("parse config: %w", err)
    }

    // Continue with initialization...
}
```

> **Note:** `libCommons.InitLocalEnvConfig()` loads `.env` files for local development. In production (containers), environment variables are injected directly and the function is a no-op. The `env.Parse()` call uses the `caarlos0/env` library to populate the struct from environment variables, respecting `envPrefix` tags for nested structs.

### Supported Types

| Go Type | Default Value | Example |
|---------|---------------|---------|
| `string` | `""` | `ServerAddress string \`env:"SERVER_ADDRESS"\`` |
| `bool` | `false` | `EnableTelemetry bool \`env:"ENABLE_TELEMETRY"\`` |
| `int`, `int8`, `int16`, `int32`, `int64` | `0` | `MaxPool int \`env:"MAX_POOL_SIZE"\`` |

### Environment Variable Naming Convention

| Category | Prefix | Example |
|----------|--------|---------|
| Application | None | `ENV_NAME`, `LOG_LEVEL`, `SERVER_ADDRESS` |
| PostgreSQL | `POSTGRES_` | `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD` |
| PostgreSQL Replica | `POSTGRES_REPLICA_` | `POSTGRES_REPLICA_HOST`, `POSTGRES_REPLICA_USER` |
| MongoDB | `MONGO_` | `MONGO_HOST`, `MONGO_NAME` |
| Redis | `REDIS_` | `REDIS_HOST`, `REDIS_PASSWORD` |
| OpenTelemetry | `OTEL_` | `OTEL_RESOURCE_SERVICE_NAME` |
| Auth Plugin | `PLUGIN_AUTH_` | `PLUGIN_AUTH_ENABLED`, `PLUGIN_AUTH_ADDRESS` |
| gRPC Services | `{SERVICE}_GRPC_` | `TRANSACTION_GRPC_ADDRESS` |

### What not to Do

```go
// FORBIDDEN: Manual os.Getenv calls scattered across code
host := os.Getenv("POSTGRES_HOST")  // DON'T do this

// FORBIDDEN: Configuration outside bootstrap
func NewService() *Service {
    dbHost := os.Getenv("POSTGRES_HOST")  // DON'T do this
}

// CORRECT: All configuration in nested Config struct, loaded once in bootstrap
type Config struct {
    Postgres PostgresConfig `envPrefix:"POSTGRES_"`
}
type PostgresConfig struct {
    Host string `env:"HOST"`  // Reads POSTGRES_HOST (prefix + field)
}

// Load with: libCommons.InitLocalEnvConfig() + env.Parse(&cfg)
```

---

