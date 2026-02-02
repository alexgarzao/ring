# Go Standards - Security

> **Module:** security.md | **Sections:** §7-8 | **Parent:** [index.md](index.md)

This module covers authentication and licensing.

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

