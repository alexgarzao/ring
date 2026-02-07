# Go Standards - Security

> **Module:** security.md | **Sections:** 5 | **Parent:** [index.md](index.md)

This module covers authentication, licensing, and secret protection.

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [Access Manager Integration](#access-manager-integration-mandatory) | lib-auth integration for authn/authz |
| 2 | [License Manager Integration](#license-manager-integration-mandatory) | lib-license-go for license validation |
| 3 | [Secret Redaction Patterns](#secret-redaction-patterns-mandatory) | Preventing credential leaks in logs |
| 4 | [SQL Safety](#sql-safety-mandatory) | SQL injection prevention and parameterized queries |
| 5 | [HTTP Security Headers](#http-security-headers-mandatory) | X-Content-Type-Options, X-Frame-Options |

---

## Access Manager Integration (MANDATORY)

All services **MUST** integrate with the Access Manager system for authentication and authorization. Services use `lib-auth` to communicate with `plugin-auth`, which handles token validation and permission enforcement.

### Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         ACCESS MANAGER                               │
├─────────────────────────────────┬───────────────────────────────────┤
│  identity                       │  plugin-auth                      │
│  (CRUD: users, apps, groups,    │  (authn + authz)                  │
│   permissions)                  │                                   │
└─────────────────────────────────┴───────────────────────────────────┘
                                    ▲
                                    │ HTTP API
                                    │
┌───────────────────────────────────┴───────────────────────────────────┐
│                              lib-auth                                  │
│  (Go library - Fiber middleware for authorization)                     │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │ import
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│  Consumer Services (midaz, plugin-fees, reporter, etc.)               │
└───────────────────────────────────────────────────────────────────────┘
```

**Key Concepts:**
- **identity**: Manages Users, Applications, Groups, and Permissions (CRUD operations)
- **plugin-auth**: Handles authentication (authn) and authorization (authz) via token validation
- **lib-auth**: Go library that services import to integrate with plugin-auth

### Required Import

```go
import (
    authMiddleware "github.com/LerianStudio/lib-auth/v2/auth/middleware"
)
```

### Required Environment Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `PLUGIN_AUTH_ADDRESS` | string | URL of plugin-auth service | `http://plugin-auth:4000` |
| `PLUGIN_AUTH_ENABLED` | bool | Enable/disable auth checks | `true` |

**For service-to-service authentication (optional):**

| Variable | Type | Description |
|----------|------|-------------|
| `CLIENT_ID` | string | OAuth2 client ID for this service |
| `CLIENT_SECRET` | string | OAuth2 client secret for this service |

### Configuration Struct

```go
// bootstrap/config.go
type Config struct {
    // ... other fields ...

    // Access Manager
    AuthAddress string `env:"PLUGIN_AUTH_ADDRESS"`
    AuthEnabled bool   `env:"PLUGIN_AUTH_ENABLED"`

    // Service-to-Service Auth (optional)
    ClientID     string `env:"CLIENT_ID"`
    ClientSecret string `env:"CLIENT_SECRET"`
}
```

### Bootstrap Integration

```go
// bootstrap/config.go
func InitServers() *Service {
    cfg := &Config{}
    if err := libCommons.SetConfigFromEnvVars(cfg); err != nil {
        panic(err)
    }

    logger := libZap.InitializeLogger()

    // ... telemetry, database initialization ...

    // Initialize Access Manager client
    auth := authMiddleware.NewAuthClient(cfg.AuthAddress, cfg.AuthEnabled, &logger)

    // Pass auth client to router
    httpApp := httpin.NewRouter(logger, telemetry, auth, handlers...)

    // ... rest of initialization ...
}
```

### Router Setup with Auth Middleware

```go
// adapters/http/in/routes.go
import (
    authMiddleware "github.com/LerianStudio/lib-auth/v2/auth/middleware"
)

const applicationName = "your-service-name"

func NewRouter(
    lg libLog.Logger,
    tl *libOpentelemetry.Telemetry,
    auth *authMiddleware.AuthClient,
    handler *YourHandler,
) *fiber.App {
    f := fiber.New(fiber.Config{
        DisableStartupMessage: true,
        ErrorHandler:          libHTTP.HandleFiberError,
    })

    // Middleware setup
    tlMid := libHTTP.NewTelemetryMiddleware(tl)
    f.Use(tlMid.WithTelemetry(tl))
    f.Use(recover.New())
    f.Use(cors.New())

    // Protected routes with authorization
    f.Post("/v1/resources", auth.Authorize(applicationName, "resources", "post"), handler.Create)
    f.Get("/v1/resources", auth.Authorize(applicationName, "resources", "get"), handler.List)
    f.Get("/v1/resources/:id", auth.Authorize(applicationName, "resources", "get"), handler.Get)
    f.Patch("/v1/resources/:id", auth.Authorize(applicationName, "resources", "patch"), handler.Update)
    f.Delete("/v1/resources/:id", auth.Authorize(applicationName, "resources", "delete"), handler.Delete)

    // Health and version (no auth required)
    f.Get("/health", libHTTP.Health)
    f.Get("/version", libHTTP.Version)

    f.Use(tlMid.EndTracingSpans)

    return f
}
```

### Authorize Middleware Parameters

```go
auth.Authorize(applicationName, resource, action)
```

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `applicationName` | string | Service identifier (must match identity registration) | `"midaz"`, `"plugin-fees"` |
| `resource` | string | Resource being accessed | `"ledgers"`, `"transactions"`, `"packages"` |
| `action` | string | HTTP method (lowercase) | `"get"`, `"post"`, `"patch"`, `"delete"` |

### Middleware Behavior

| Scenario | HTTP Response |
|----------|---------------|
| Auth disabled (`PLUGIN_AUTH_ENABLED=false`) | Skips check, calls `next()` |
| Missing Authorization header | `401 Unauthorized` |
| Token invalid or expired | `401 Unauthorized` |
| User lacks permission | `403 Forbidden` |
| User authorized | Calls `next()` |

### Service-to-Service Authentication

When a service needs to call another service (e.g., plugin-fees calling midaz), use `GetApplicationToken`:

```go
// pkg/net/http/external_service.go
import (
    "context"
    "os"
    authMiddleware "github.com/LerianStudio/lib-auth/v2/auth/middleware"
)

type ExternalServiceClient struct {
    authClient *authMiddleware.AuthClient
    baseURL    string
}

func (c *ExternalServiceClient) CallExternalService(ctx context.Context) (*Response, error) {
    // Get application token using client credentials flow
    token, err := c.authClient.GetApplicationToken(
        ctx,
        os.Getenv("CLIENT_ID"),
        os.Getenv("CLIENT_SECRET"),
    )
    if err != nil {
        return nil, fmt.Errorf("failed to get application token: %w", err)
    }

    // Create request with token
    req, _ := http.NewRequestWithContext(ctx, "GET", c.baseURL+"/v1/resource", nil)
    req.Header.Set("Authorization", "Bearer "+token)
    req.Header.Set("Content-Type", "application/json")

    // Inject trace context for distributed tracing
    libOpentelemetry.InjectHTTPContext(&req.Header, ctx)

    resp, err := c.httpClient.Do(req)
    // ... handle response
}
```

### Common Headers

| Header | Purpose | Example |
|--------|---------|---------|
| `Authorization` | Bearer token for authentication | `Bearer eyJhbG...` |
| `X-Organization-Id` | Organization context for multi-tenancy | UUID |
| `X-Ledger-Id` | Ledger context (when applicable) | UUID |

### Organization ID Middleware Pattern

```go
// adapters/http/in/middlewares.go
const OrgIDHeaderParameter = "X-Organization-Id"

func ParseHeaderParameters(c *fiber.Ctx) error {
    headerParam := c.Get(OrgIDHeaderParameter)
    if headerParam == "" {
        return libHTTP.WithError(c, ErrMissingOrganizationID)
    }

    parsedUUID, err := uuid.Parse(headerParam)
    if err != nil {
        return libHTTP.WithError(c, ErrInvalidOrganizationID)
    }

    c.Locals(OrgIDHeaderParameter, parsedUUID)
    return c.Next()
}
```

### Complete Route Example with Headers

```go
// Route with auth + header parsing
f.Post("/v1/packages",
    auth.Authorize(applicationName, "packages", "post"),
    ParseHeaderParameters,
    handler.CreatePackage)
```

### What not to Do

```go
// FORBIDDEN: Hardcoded tokens
req.Header.Set("Authorization", "Bearer hardcoded-token-here")  // never

// FORBIDDEN: Skipping auth on protected endpoints
f.Post("/v1/sensitive-data", handler.Create)  // Missing auth.Authorize

// FORBIDDEN: Using wrong application name
auth.Authorize("wrong-app-name", "resource", "post")  // Must match identity registration

// FORBIDDEN: Direct calls to plugin-auth API
http.Post("http://plugin-auth:4000/v1/authorize", ...)  // Use lib-auth instead

// CORRECT: Always use lib-auth for auth operations
auth.Authorize(applicationName, "resource", "post")
token, _ := auth.GetApplicationToken(ctx, clientID, clientSecret)
```

### Testing with Auth Disabled

For local development and testing, disable auth via environment:

```bash
PLUGIN_AUTH_ENABLED=false
```

When disabled, `auth.Authorize()` middleware calls `next()` without validation.

---

## License Manager Integration (MANDATORY)

All licensed plugins/products **MUST** integrate with the License Manager system for license validation. Services use `lib-license-go` to validate licenses against the Lerian backend, with support for both global and multi-organization modes.

### Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────────┐
│                       LICENSE MANAGER                               │
├─────────────────────────────────────────────────────────────────────┤
│  Lerian License Backend (AWS API Gateway)                           │
│  - Validates license keys                                           │
│  - Returns plugin entitlements                                      │
│  - Supports global and per-organization licenses                    │
└─────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │ HTTPS API
                                    │
┌───────────────────────────────────┴───────────────────────────────────┐
│                           lib-license-go                              │
│  (Go library - Fiber middleware + gRPC interceptors)                  │
│  - Ristretto in-memory cache                                          │
│  - Weekly background refresh                                          │
│  - Startup validation (fail-fast)                                     │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │ import
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│  Licensed Services (plugin-fees, reporter, etc.)                      │
└───────────────────────────────────────────────────────────────────────┘
```

**Key Concepts:**
- **Global Mode**: Single license key validates entire plugin (use `ORGANIZATION_IDS=global`)
- **Multi-Org Mode**: Per-organization license validation via `X-Organization-Id` header
- **Fail-Fast**: Service panics at startup if no valid license found

### Required Import

```go
import (
    libLicense "github.com/LerianStudio/lib-license-go/v2/middleware"
)
```

### Required Environment Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `LICENSE_KEY` | string | License key for this plugin | `lic_xxxxxxxxxxxx` |
| `ORGANIZATION_IDS` | string | Comma-separated org IDs or "global" | `org1,org2` or `global` |

### Configuration Struct

```go
// bootstrap/config.go
type Config struct {
    // ... other fields ...

    // License Manager
    LicenseKey      string `env:"LICENSE_KEY"`
    OrganizationIDs string `env:"ORGANIZATION_IDS"`
}
```

### Bootstrap Integration

```go
// bootstrap/config.go
import (
    libLicense "github.com/LerianStudio/lib-license-go/v2/middleware"
)

func InitServers() *Service {
    cfg := &Config{}
    if err := libCommons.SetConfigFromEnvVars(cfg); err != nil {
        panic(err)
    }

    logger := libZap.InitializeLogger()

    // ... telemetry, database initialization ...

    // Initialize License Manager client
    licenseClient := libLicense.NewLicenseClient(
        constant.ApplicationName,  // e.g., "plugin-fees"
        cfg.LicenseKey,
        cfg.OrganizationIDs,
        &logger,
    )

    // Pass license client to router and server
    httpApp := httpin.NewRouter(logger, telemetry, auth, licenseClient, handlers...)
    serverAPI := NewServer(cfg, httpApp, logger, telemetry, licenseClient)

    // ... rest of initialization ...
}
```

### Router Setup with License Middleware

```go
// adapters/http/in/routes.go
import (
    libHTTP "github.com/LerianStudio/lib-commons/v2/commons/net/http"
    libLicense "github.com/LerianStudio/lib-license-go/v2/middleware"
)

func NewRoutes(lg log.Logger, tl *opentelemetry.Telemetry, handler *YourHandler, lc *libLicense.LicenseClient) *fiber.App {
    f := fiber.New(fiber.Config{
        DisableStartupMessage: true,
        ErrorHandler: func(ctx *fiber.Ctx, err error) error {
            return libHTTP.HandleFiberError(ctx, err)
        },
    })
    tlMid := libHTTP.NewTelemetryMiddleware(tl)

    // License middleware - applies GLOBALLY (must be early in chain)
    f.Use(lc.Middleware())

    // Other middleware
    f.Use(tlMid.WithTelemetry(tl))
    f.Use(cors.New())
    f.Use(libHTTP.WithHTTPLogging(libHTTP.WithCustomLogger(lg)))

    // Routes
    v1 := f.Group("/v1")
    v1.Post("/resources", handler.Create)
    v1.Get("/resources", handler.List)

    // Health and version (automatically skipped by license middleware)
    f.Get("/health", libHTTP.Ping)
    f.Get("/version", libHTTP.Version)

    f.Use(tlMid.EndTracingSpans)

    return f
}
```

**Note:** License middleware should be applied early in the middleware chain. It automatically skips `/health`, `/version`, and `/swagger/` paths.

### Server Integration with Graceful Shutdown

```go
// bootstrap/server.go
import (
    libCommonsLicense "github.com/LerianStudio/lib-commons/v2/commons/license"
    libLicense "github.com/LerianStudio/lib-license-go/v2/middleware"
)

type Server struct {
    app           *fiber.App
    serverAddress string
    license       *libCommonsLicense.ManagerShutdown
    logger        libLog.Logger
    telemetry     libOpentelemetry.Telemetry
}

func NewServer(cfg *Config, app *fiber.App, logger libLog.Logger, telemetry *libOpentelemetry.Telemetry, licenseClient *libLicense.LicenseClient) *Server {
    return &Server{
        app:           app,
        serverAddress: cfg.ServerAddress,
        license:       licenseClient.GetLicenseManagerShutdown(),
        logger:        logger,
        telemetry:     *telemetry,
    }
}

func (s *Server) Run(l *libCommons.Launcher) error {
    // License manager integrated into graceful shutdown
    libCommonsServer.NewServerManager(s.license, &s.telemetry, s.logger).
        WithHTTPServer(s.app, s.serverAddress).
        StartWithGracefulShutdown()

    return nil
}
```

### Default Skip Paths

The license middleware automatically skips validation for:

| Path | Reason |
|------|--------|
| `/health` | Health checks must always respond |
| `/version` | Version endpoint is public |
| `/swagger/` | API documentation is public |

### gRPC Integration (If Applicable)

```go
// For gRPC services
import (
    "google.golang.org/grpc"
    libLicense "github.com/LerianStudio/lib-license-go/v2/middleware"
)

func NewGRPCServer(licenseClient *libLicense.LicenseClient) *grpc.Server {
    server := grpc.NewServer(
        grpc.UnaryInterceptor(licenseClient.UnaryServerInterceptor()),
        grpc.StreamInterceptor(licenseClient.StreamServerInterceptor()),
    )

    // Register your services
    pb.RegisterYourServiceServer(server, &yourServiceImpl{})

    return server
}
```

### Middleware Behavior

| Mode | Startup | Per-Request |
|------|---------|-------------|
| Global (`ORGANIZATION_IDS=global`) | Validates license, panics if invalid | Skips validation, calls `next()` |
| Multi-Org | Validates all orgs, panics if none valid | Validates `X-Organization-Id` header |

### Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `LCS-0001` | 500 | Internal server error during validation |
| `LCS-0002` | 400 | No organization IDs configured |
| `LCS-0003` | 403 | No valid licenses found for any organization |
| `LCS-0010` | 400 | Missing `X-Organization-Id` header |
| `LCS-0011` | 400 | Unknown organization ID |
| `LCS-0012` | 403 | Failed to validate organization license |
| `LCS-0013` | 403 | Organization license is invalid or expired |

### What not to Do

```go
// FORBIDDEN: Hardcoded license keys
licenseClient := libLicense.NewLicenseClient(appName, "hardcoded-key", orgIDs, &logger)  // never

// FORBIDDEN: Skipping license middleware on licensed routes
f.Post("/v1/paid-feature", handler.Create)  // Missing lc.Middleware()

// FORBIDDEN: Not integrating shutdown manager
libCommonsServer.NewServerManager(nil, &s.telemetry, s.logger)  // Missing license shutdown

// CORRECT: Always use environment variables and integrate shutdown
licenseClient := libLicense.NewLicenseClient(appName, cfg.LicenseKey, cfg.OrganizationIDs, &logger)
libCommonsServer.NewServerManager(s.license, &s.telemetry, s.logger)
```

### Testing with License Disabled

For local development without license validation, you can omit the license client initialization or use a mock. The service will panic at startup if `LICENSE_KEY` is set but invalid.

**Tip:** For development, either:
1. Use a valid development license key
2. Comment out the license middleware during local development
3. Use the development license server: `IS_DEVELOPMENT=true`

---

## Secret Redaction Patterns (MANDATORY)

**⛔ HARD GATE:** Credentials, connection strings, API keys, and tokens MUST NOT appear in logs. Exposing AMQP, database DSNs, or API credentials in logs creates security vulnerabilities.

### FORBIDDEN Patterns (CRITICAL)

```go
// ❌ FORBIDDEN: Logging connection strings
logger.Infof("Connecting to: %s", amqpURI)  // EXPOSES: amqp://user:password@host:5672

// ❌ FORBIDDEN: Logging DSN/connection strings
logger.Infof("Database: %s", databaseDSN)  // EXPOSES: postgres://user:password@host/db

// ❌ FORBIDDEN: Logging environment variables with secrets
for k, v := range os.Environ() {
    logger.Infof("%s=%s", k, v)  // EXPOSES: DB_PASSWORD, API_KEY, etc.
}

// ❌ FORBIDDEN: Logging config struct with secrets
logger.Infof("Config: %+v", cfg)  // EXPOSES: all fields including passwords

// ❌ FORBIDDEN: Logging HTTP headers with auth
logger.Infof("Headers: %v", req.Header)  // EXPOSES: Authorization header

// ❌ FORBIDDEN: Using fmt.Printf for connection strings
fmt.Printf("AMQP: %s\n", amqpURI)  // EXPOSES: credentials to stdout
```

### Correct Patterns (REQUIRED)

```go
// ✅ CORRECT: Redact connection strings before logging
func redactConnectionString(uri string) string {
    // amqp://user:password@host:5672 → amqp://***:***@host:5672
    u, err := url.Parse(uri)
    if err != nil {
        return "[invalid-uri]"
    }
    if u.User != nil {
        u.User = url.UserPassword("***", "***")
    }
    return u.String()
}

logger.Infof("Connecting to: %s", redactConnectionString(amqpURI))

// ✅ CORRECT: Log only safe portions
logger.Infof("Connecting to RabbitMQ at %s:%s", cfg.RabbitMQHost, cfg.RabbitMQPort)

// ✅ CORRECT: Redact config before logging
type SafeConfig struct {
    Host     string `json:"host"`
    Port     string `json:"port"`
    Database string `json:"database"`
    // Password omitted
}
logger.Infof("Config: %+v", SafeConfig{Host: cfg.Host, Port: cfg.Port, Database: cfg.Database})

// ✅ CORRECT: Use lib-commons logger (automatically redacts sensitive patterns)
logger.Infof("Service started on %s", cfg.ServerAddress)  // No secrets in this field
```

### Secrets that MUST NOT be Logged

| Secret Type | Example Pattern | Detection Regex |
|-------------|-----------------|-----------------|
| AMQP URI | `amqp://user:pass@host` | `amqp://[^:]+:[^@]+@` |
| Postgres DSN | `postgres://user:pass@host/db` | `postgres://[^:]+:[^@]+@` |
| MongoDB URI | `mongodb://user:pass@host` | `mongodb://[^:]+:[^@]+@` |
| Redis URI | `redis://user:pass@host` | `redis://[^:]+:[^@]+@` |
| API Keys | `sk_live_xxxxx`, `api_key=xxxxx` | `(sk_|api[_-]?key)` (use with `grep -E`) |
| Bearer Tokens | `Authorization: Bearer xxx` | `Bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+` |
| AWS Credentials | `AKIA...`, `aws_secret_access_key` | `AKIA[A-Z0-9]{16}` |

### Detection Commands (MANDATORY)

Use **extended regex** for the API Keys pattern: run `grep -E` with pattern `(sk_|api[_-]?key)`. For basic grep (no `-E`), escape alternation and quantifiers: `sk_\|api[_-]\?key`. Prefer `grep -E '(sk_|api[_-]?key)'` for clarity. See table above for the exact pattern and this section for which form to use.

```bash
# MANDATORY: Run before every PR that touches config or logging

# Find direct connection string logging
grep -rn "log.*amqp://\|fmt.Print.*amqp://\|logger.*amqp://" --include="*.go"
grep -rn "log.*postgres://\|fmt.Print.*postgres://\|logger.*postgres://" --include="*.go"
grep -rn "log.*mongodb://\|fmt.Print.*mongodb://\|logger.*mongodb://" --include="*.go"

# Find password logging
grep -rn "password.*log\|log.*password" --include="*.go" -i

# Find config struct logging (review each match)
grep -rn 'Infof.*%\+v.*cfg\|Printf.*%\+v.*config' --include="*.go"

# Find environment variable dumps
grep -rn "os.Environ\(\)" --include="*.go"

# Expected: 0 matches for connection strings with credentials
# If any match found: STOP. Fix before proceeding.
```

### lib-commons Logger Configuration

When using lib-commons logger, configure secret redaction:

```go
// lib-commons/v2 automatically redacts certain patterns
// But you MUST NOT pass secrets to the logger in the first place

// ❌ Still FORBIDDEN even with lib-commons:
logger.Infof("Config: %+v", cfg)  // May contain secrets

// ✅ CORRECT: Only log safe fields
logger.Infof("Server starting on %s", cfg.ServerAddress)
```

### Environment Variable Handling

```go
// ❌ FORBIDDEN: Iterating and logging all env vars
for _, env := range os.Environ() {
    log.Println(env)
}

// ✅ CORRECT: Log only specific, safe env vars
logger.Infof("Environment: %s, Server: %s", os.Getenv("ENV_NAME"), os.Getenv("SERVER_ADDRESS"))

// ✅ CORRECT: Use structured config loading (lib-commons)
func loadConfig() (*Config, error) {
    cfg := &Config{}
    if err := libCommons.SetConfigFromEnvVars(cfg); err != nil {
        return nil, fmt.Errorf("load config: %w", err)
    }
    return cfg, nil
}
```

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "We need connection strings for debugging" | Logs are stored and shared. Secrets leak to CloudWatch, Grafana, S3. | **Log redacted strings only** |
| "Only developers see logs" | Logs go to centralized systems accessible by many. | **Redact all secrets** |
| "It's just the dev environment" | Dev logs train bad habits. Same code goes to prod. | **Redact in all environments** |
| "The password is rotated anyway" | Rotation doesn't help if old password is in logs. | **Never log secrets** |
| "I'm just debugging locally" | Local debugging code gets committed. | **Remove debug logging before commit** |
| "lib-commons handles it" | lib-commons can't redact what you pass to it. | **Don't pass secrets to logger** |

### Verification Checklist (Before PR)

```text
Before submitting PR that adds logging:

[ ] Did I search for connection string patterns in my changes?
[ ] Did I verify no passwords are logged (even in debug statements)?
[ ] Did I avoid logging entire config structs (%+v)?
[ ] Did I avoid logging HTTP headers that may contain Authorization?
[ ] Did I run the detection commands above?

If any checkbox is unchecked → FIX before submitting.
```

---

## SQL Safety (MANDATORY)

**⛔ HARD GATE:** All database queries MUST use parameterized queries. String concatenation in SQL is FORBIDDEN and creates injection vulnerabilities.

### FORBIDDEN Patterns (CRITICAL)

```go
// ❌ FORBIDDEN: String concatenation in SQL
query := "SELECT * FROM users WHERE id = '" + userID + "'"
query := fmt.Sprintf("SELECT * FROM users WHERE email = '%s'", email)
query := "DELETE FROM orders WHERE status = " + status

// ❌ FORBIDDEN: Building WHERE clauses with user input
whereClause := "name LIKE '%" + searchTerm + "%'"
query := "SELECT * FROM products WHERE " + whereClause

// ❌ FORBIDDEN: Dynamic table/column names from user input
tableName := req.Query("table")
query := fmt.Sprintf("SELECT * FROM %s", tableName)

// ❌ FORBIDDEN: Raw queries with string interpolation
db.Raw("SELECT * FROM users WHERE role = '" + role + "'")
```

### Correct Patterns (REQUIRED)

```go
// ✅ CORRECT: Parameterized queries with pgx
row := conn.QueryRow(ctx,
    "SELECT id, name, email FROM users WHERE id = $1",
    userID,
)

// ✅ CORRECT: Multiple parameters
rows, err := conn.Query(ctx,
    "SELECT * FROM orders WHERE user_id = $1 AND status = $2 AND created_at > $3",
    userID, status, startDate,
)

// ✅ CORRECT: IN clause with pgx.Array
rows, err := conn.Query(ctx,
    "SELECT * FROM products WHERE id = ANY($1)",
    pgx.Array(productIDs),
)

// ✅ CORRECT: LIKE with parameterized pattern
searchPattern := "%" + sanitizeSearchTerm(term) + "%"
rows, err := conn.Query(ctx,
    "SELECT * FROM products WHERE name ILIKE $1",
    searchPattern,
)

// ✅ CORRECT: Using query builders (squirrel)
query, args, err := sq.Select("id", "name").
    From("users").
    Where(sq.Eq{"status": status}).
    Where(sq.Like{"email": "%" + domain}).
    ToSql()
rows, err := conn.Query(ctx, query, args...)

// ✅ CORRECT: Dynamic columns with whitelist
allowedColumns := map[string]bool{"name": true, "email": true, "created_at": true}
if !allowedColumns[sortColumn] {
    sortColumn = "created_at" // Default to safe column
}
query := fmt.Sprintf("SELECT * FROM users ORDER BY %s", sortColumn)
```

### pgx Parameterization Reference

| Pattern | Syntax | Example |
|---------|--------|---------|
| Single value | `$1` | `WHERE id = $1` |
| Multiple values | `$1, $2, $3` | `WHERE a = $1 AND b = $2` |
| Array/IN clause | `ANY($1)` with `pgx.Array()` | `WHERE id = ANY($1)` |
| NULL check | `$1 IS NULL OR col = $1` | Optional filters |

### Detection Commands (MANDATORY)

```bash
# MANDATORY: Run before every PR that touches database code

# Find string concatenation in SQL contexts
grep -rn 'Sprintf.*SELECT\|Sprintf.*INSERT\|Sprintf.*UPDATE\|Sprintf.*DELETE' --include="*.go"
grep -rn 'SELECT.*" \+ \|INSERT.*" \+ \|UPDATE.*" \+ \|DELETE.*" \+ ' --include="*.go"

# Find Raw() with string interpolation
grep -rn 'Raw(".*" \+\|Raw(fmt.Sprintf' --include="*.go"

# Find fmt in SQL files
grep -rn 'fmt.Sprintf.*FROM\|fmt.Sprintf.*WHERE' --include="*.go"

# Expected: 0 matches
# If any match found: STOP. Fix before proceeding.
```

### Whitelist Pattern for Dynamic Identifiers

```go
// When table/column names must be dynamic (e.g., multi-tenant schemas)
// ALWAYS use explicit whitelists

var allowedTables = map[string]bool{
    "users":    true,
    "orders":   true,
    "products": true,
}

func queryTable(ctx context.Context, conn *pgx.Conn, table string, id string) (*Row, error) {
    // ✅ CORRECT: Whitelist validation before any SQL
    if !allowedTables[table] {
        return nil, fmt.Errorf("invalid table: %s", table)
    }

    // Table name is safe (from whitelist), ID is parameterized
    query := fmt.Sprintf("SELECT * FROM %s WHERE id = $1", table)
    return conn.QueryRow(ctx, query, id), nil
}
```

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Input is validated elsewhere" | Defense in depth. SQL injection at query level is catastrophic. | **Always parameterize** |
| "Only internal services call this" | Internal services can be compromised. Assume hostile input. | **Always parameterize** |
| "The value is a UUID/integer" | Type coercion can fail. Attacker controls types. | **Always parameterize** |
| "Performance is better with string concat" | False. Prepared statements are often faster. Security > micro-optimization. | **Always parameterize** |
| "It's just a read query" | SQL injection enables data exfiltration, not just writes. | **Always parameterize** |
| "Query builder handles it" | Verify the builder parameterizes. Some don't. | **Check generated SQL** |

### Verification Checklist (Before PR)

```text
Before submitting PR that touches database queries:

[ ] Did I use parameterized queries for all user input?
[ ] Did I run the detection commands above?
[ ] Did I whitelist any dynamic table/column names?
[ ] Did I avoid string concatenation in SQL strings?
[ ] Did I verify query builders generate parameterized output?

If any checkbox is unchecked → FIX before submitting.
```

---

## HTTP Security Headers (MANDATORY)

**⛔ HARD GATE:** All HTTP services MUST set security headers to prevent common web vulnerabilities. Missing headers expose the application to clickjacking, MIME sniffing, and other attacks.

### Required Headers

| Header | Required Value | Purpose |
|--------|----------------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME type sniffing attacks |
| `X-Frame-Options` | `DENY` | Prevents clickjacking via iframe embedding |

### Implementation Pattern (Fiber)

```go
// internal/adapters/http/in/middleware.go

func SecurityHeaders() fiber.Handler {
    return func(c *fiber.Ctx) error {
        // MANDATORY: Prevent MIME sniffing
        c.Set("X-Content-Type-Options", "nosniff")

        // MANDATORY: Prevent clickjacking
        c.Set("X-Frame-Options", "DENY")

        return c.Next()
    }
}

// Apply in router setup
func NewRouter(app *fiber.App) {
    app.Use(SecurityHeaders())
    // ... other middleware and routes
}
```

### Alternative: lib-commons Integration

If using lib-commons server setup, headers can be configured at server level:

```go
// bootstrap/fiber.server.go
serverConfig := libServer.Config{
    // ... other config
    SecurityHeaders: libServer.SecurityHeaders{
        XContentTypeOptions: "nosniff",
        XFrameOptions:       "DENY",
    },
}
```

### Detection Commands

```bash
# Find if security headers are set
grep -rn "X-Content-Type-Options\|X-Frame-Options" --include="*.go" ./internal

# Verify middleware registration
grep -rn "SecurityHeaders\|security.*middleware" --include="*.go" ./internal

# Expected: At least one match for each header
```

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "We're behind a reverse proxy" | Defense in depth. App should protect itself. | **Add headers** |
| "It's just an internal API" | Internal APIs can be accessed by compromised services. | **Add headers** |
| "Headers don't affect JSON APIs" | MIME sniffing affects all responses. Clickjacking targets browsers. | **Add headers** |
| "We'll add it later" | Later = security incident. Add now. | **Add headers immediately** |

---

