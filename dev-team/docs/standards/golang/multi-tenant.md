# Go Standards - Multi-Tenant

> **Module:** multi-tenant.md | **Sections:** §24 | **Parent:** [index.md](index.md)

This module covers multi-tenant patterns with Tenant Manager.

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [Multi-Tenant Patterns (CONDITIONAL)](#multi-tenant-patterns-conditional) | Configuration, Tenant Manager API, middleware, context injection, repository adaptation |
| 2 | [Tenant Isolation Verification (⚠️ CONDITIONAL)](#tenant-isolation-verification-conditional) | IDOR prevention, tenant verification in queries |
| 24 | [Multi-Tenant Message Queue Consumers (Lazy Mode)](#multi-tenant-message-queue-consumers-lazy-mode) | Lazy consumer initialization, on-demand connection, exponential backoff |

---

## Multi-Tenant Patterns (CONDITIONAL)

**CONDITIONAL:** Only implement if `MULTI_TENANT_ENABLED=true` is required for your service.

### Required lib-commons Version

Multi-tenant support requires **lib-commons v3** (`github.com/LerianStudio/lib-commons/v3`). The `tenant-manager` package does not exist in v2.

| lib-commons version | Multi-tenant support | Package path |
|--------------------|-----------------------|-------------|
| **v2** (`lib-commons/v2`) | Not available | N/A — no `tenant-manager` package |
| **v3** (`lib-commons/v3`) | Full support | `github.com/LerianStudio/lib-commons/v3/commons/tenant-manager` |

**Migration from v2 to v3:**

Services currently on lib-commons v2 MUST upgrade to v3 before implementing multi-tenant. The upgrade involves:

1. Update `go.mod`: `github.com/LerianStudio/lib-commons/v2` -> `github.com/LerianStudio/lib-commons/v3`
2. Update all import paths: `lib-commons/v2/commons/...` -> `lib-commons/v3/commons/...`
3. Add the `tenant-manager` package imports where needed

```bash
# Update go.mod
go get github.com/LerianStudio/lib-commons/v3@latest

# Update import paths across the codebase
find . -name "*.go" -exec sed -i '' 's|lib-commons/v2|lib-commons/v3|g' {} +

# Verify build
go build ./...
```

### When to Use Multi-Tenant Mode

| Scenario | Mode | Configuration |
|----------|------|---------------|
| Single customer deployment | Single-tenant | `MULTI_TENANT_ENABLED=false` (default) |
| SaaS with shared infrastructure | Multi-tenant | `MULTI_TENANT_ENABLED=true` |
| Multiple isolated databases per customer | Multi-tenant | Requires Tenant Manager |

### Environment Variables

| Env Var | Description | Default | Required |
|---------|-------------|---------|----------|
| `MULTI_TENANT_ENABLED` | Enable multi-tenant mode | `false` | Yes |
| `MULTI_TENANT_URL` | Tenant Manager service URL | - | If multi-tenant |
| `MULTI_TENANT_ENVIRONMENT` | Deployment environment for cache key segmentation | `staging` | If multi-tenant |
| `MULTI_TENANT_MAX_TENANT_POOLS` | Soft limit for tenant connection pools (LRU eviction) | `100` | No |
| `MULTI_TENANT_IDLE_TIMEOUT_SEC` | Seconds before idle tenant connection is eviction-eligible | `300` | No |
| `MULTI_TENANT_CIRCUIT_BREAKER_THRESHOLD` | Consecutive failures before circuit breaker opens | `5` | No |
| `MULTI_TENANT_CIRCUIT_BREAKER_TIMEOUT_SEC` | Seconds before circuit breaker resets (half-open) | `30` | No |

**Example `.env` for multi-tenant:**
```bash
MULTI_TENANT_ENABLED=true
MULTI_TENANT_URL=http://tenant-manager:4003
MULTI_TENANT_ENVIRONMENT=production
MULTI_TENANT_MAX_TENANT_POOLS=100
MULTI_TENANT_IDLE_TIMEOUT_SEC=300
MULTI_TENANT_CIRCUIT_BREAKER_THRESHOLD=5
MULTI_TENANT_CIRCUIT_BREAKER_TIMEOUT_SEC=30
```

### Configuration

```go
// internal/bootstrap/config.go
type Config struct {
    // Multi-Tenant Configuration
    MultiTenantEnabled                  bool   `env:"MULTI_TENANT_ENABLED" default:"false"`
    MultiTenantURL                      string `env:"MULTI_TENANT_URL"`
    MultiTenantEnvironment              string `env:"MULTI_TENANT_ENVIRONMENT" default:"staging"`
    MultiTenantMaxTenantPools           int    `env:"MULTI_TENANT_MAX_TENANT_POOLS" default:"100"`
    MultiTenantIdleTimeoutSec           int    `env:"MULTI_TENANT_IDLE_TIMEOUT_SEC" default:"300"`
    MultiTenantCircuitBreakerThreshold  int    `env:"MULTI_TENANT_CIRCUIT_BREAKER_THRESHOLD" default:"5"`
    MultiTenantCircuitBreakerTimeoutSec int    `env:"MULTI_TENANT_CIRCUIT_BREAKER_TIMEOUT_SEC" default:"30"`

    // PostgreSQL Primary (used as default connection in single-tenant mode)
    PrimaryDBHost     string `env:"DB_HOST"`
    PrimaryDBUser     string `env:"DB_USER"`
    PrimaryDBPassword string `env:"DB_PASSWORD"`
    PrimaryDBName     string `env:"DB_NAME"`
    PrimaryDBPort     string `env:"DB_PORT"`
    PrimaryDBSSLMode  string `env:"DB_SSLMODE"`
}
```

### Tenant Manager Service API

The Tenant Manager is an external service that stores database credentials per tenant. All connection managers in lib-commons call this API to resolve tenant-specific connections.

**Endpoints:**

| Method | Path | Returns | Purpose |
|--------|------|---------|---------|
| `GET` | `/tenants/{tenantID}/services/{service}/settings` | `TenantConfig` | Full tenant configuration with DB credentials |
| `GET` | `/tenants/active?service={service}` | `[]*TenantSummary` | List of active tenants (fallback for discovery) |

**Tenant Discovery (for lazy consumer mode):**
1. Primary: Redis `SMEMBERS "tenant-manager:tenants:active"` (fast, <1ms)
2. Fallback: HTTP `GET /tenants/active?service={service}` (slower, network call)

### TenantConfig Data Model

The Tenant Manager returns this structure for each tenant. The `Databases` map is keyed by **module name** (e.g., `"onboarding"`, `"transaction"`).

```go
type TenantConfig struct {
    ID            string                         // Tenant UUID
    TenantSlug    string                         // Human-readable slug
    IsolationMode string                         // "isolated" (default) or "schema"
    Databases     map[string]DatabaseConfig       // module -> config
    Messaging     *MessagingConfig               // RabbitMQ config (optional)
}

type DatabaseConfig struct {
    PostgreSQL         *PostgreSQLConfig
    PostgreSQLReplica  *PostgreSQLConfig    // Read replica (optional)
    MongoDB            *MongoDBConfig
    ConnectionSettings *ConnectionSettings  // Per-tenant pool overrides (optional)
}

// ConnectionSettings holds per-tenant database connection pool settings.
// When present, these values override the global defaults on PostgresManager/MongoManager.
// If nil (e.g., older tenant associations), global defaults apply.
type ConnectionSettings struct {
    MaxOpenConns int `json:"maxOpenConns"`
    MaxIdleConns int `json:"maxIdleConns"`
}
```

**Isolation Modes:**

| Mode | Database | Schema | Connection String | When to Use |
|------|----------|--------|-------------------|-------------|
| `isolated` (default) | Separate database per tenant | Default `public` schema | Standard connection | Strong isolation, recommended |
| `schema` | Shared database | Schema per tenant | Adds `options=-csearch_path="{schema}"` | Cost optimization, weaker isolation |

### Connection Pool Management

All connection managers (PostgreSQL, MongoDB, RabbitMQ) use **LRU eviction with soft limits**:

- **Soft limit** (`WithMaxTenantPools`): When the pool reaches this size and a new tenant needs a connection, only connections idle longer than the timeout are evicted. If all connections are active, the pool grows beyond the limit.
- **Idle timeout** (`WithIdleTimeout`): Connections not accessed within this window become eligible for eviction. Default: 5 minutes.
- **Connection health**: Cached connections are pinged before reuse (3s timeout). Stale connections are recreated transparently.

The Tenant Manager HTTP client supports an optional **circuit breaker** (`WithCircuitBreaker`):
- After N consecutive failures, the circuit opens and requests fail fast with `ErrCircuitBreakerOpen`
- After the timeout, the circuit enters half-open state and allows one request through
- On success, the circuit resets to closed

### JWT Tenant Extraction

**Claim key:** `tenantId` (camelCase, hardcoded)

**The `tenantId` is the REAL tenant identifier.** It identifies the client/customer. Other IDs like `organization_id` represent entities WITHIN a tenant (multi-organization support) and do NOT provide tenant-level isolation.

```go
// internal/bootstrap/middleware.go
func extractTenantIDFromToken(c *fiber.Ctx) (string, error) {
    // Use lib-commons helper for token extraction
    accessToken := libHTTP.ExtractTokenFromHeader(c)
    if accessToken == "" {
        return "", errors.New("no authorization token provided")
    }

    // Parse without validation (validation done by auth middleware)
    token, _, err := new(jwt.Parser).ParseUnverified(accessToken, jwt.MapClaims{})
    if err != nil {
        return "", err
    }

    claims, ok := token.Claims.(jwt.MapClaims)
    if !ok {
        return "", errors.New("invalid token claims format")
    }

    // Extract tenantId (camelCase only - no fallbacks)
    tenantID, ok := claims["tenantId"].(string)
    if !ok || tenantID == "" {
        return "", errors.New("tenantId claim not found in token")
    }

    return tenantID, nil
}
```

### Generic TenantMiddleware (Standard Pattern)

**This is the standard pattern for all services.** The lib-commons `TenantMiddleware` handles JWT extraction, tenant resolution, and context injection automatically.

```go
// internal/bootstrap/config.go
func initService(cfg *Config) {
    // 1. Create Tenant Manager HTTP client (with optional circuit breaker)
    var clientOpts []tenantmanager.ClientOption
    if cfg.MultiTenantCircuitBreakerThreshold > 0 {
        clientOpts = append(clientOpts,
            tenantmanager.WithCircuitBreaker(
                cfg.MultiTenantCircuitBreakerThreshold,
                time.Duration(cfg.MultiTenantCircuitBreakerTimeoutSec)*time.Second,
            ),
        )
    }
    tmClient := tenantmanager.NewClient(cfg.MultiTenantURL, logger, clientOpts...)

    idleTimeout := time.Duration(cfg.MultiTenantIdleTimeoutSec) * time.Second

    // 2. Create PostgreSQL manager (one per service or per module)
    pgManager := tenantmanager.NewPostgresManager(tmClient, "my-service",
        tenantmanager.WithModule("my-module"),
        tenantmanager.WithPostgresLogger(logger),
        tenantmanager.WithMaxTenantPools(cfg.MultiTenantMaxTenantPools),
        tenantmanager.WithIdleTimeout(idleTimeout),
    )

    // 3. Create MongoDB manager (optional)
    mongoManager := tenantmanager.NewMongoManager(tmClient, "my-service",
        tenantmanager.WithMongoModule("my-module"),
        tenantmanager.WithMongoLogger(logger),
        tenantmanager.WithMongoMaxTenantPools(cfg.MultiTenantMaxTenantPools),
        tenantmanager.WithMongoIdleTimeout(idleTimeout),
    )

    // 4. Create and register middleware
    tenantMid := tenantmanager.NewTenantMiddleware(
        tenantmanager.WithPostgresManager(pgManager),
        tenantmanager.WithMongoManager(mongoManager),  // optional
    )
    app.Use(tenantMid.WithTenantDB)
}
```

**What the middleware does internally:**
1. Extracts `Authorization: Bearer {token}` header
2. Parses JWT (unverified — auth middleware already validated it)
3. Extracts `tenantId` claim
4. Calls `PostgresManager.GetConnection(ctx, tenantID)` to resolve tenant-specific DB
5. Stores tenant ID and DB connection in context
6. If MongoDB manager is set, resolves and stores MongoDB connection
7. Calls `c.Next()`

**In repositories, use context-based getters:**

```go
// Single-module service: use generic getter
db, err := tenantmanager.GetPostgresForTenant(ctx)

// MongoDB
mongoDB, err := tenantmanager.GetMongoForTenant(ctx)

// Redis key prefixing
key := tenantmanager.GetKeyFromContext(ctx, "cache-key")
// -> "tenant:{tenantId}:cache-key"

// Get tenant ID directly
tenantID := tenantmanager.GetTenantID(ctx)
```

### Database Connection in Repositories

Repositories use context-based getters to retrieve tenant connections:

```go
// internal/adapters/postgres/entity/entity.postgresql.go
func (r *EntityPostgreSQLRepository) Create(ctx context.Context, entity *mmodel.Entity) (*mmodel.Entity, error) {
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "postgres.create_entity")
    defer span.End()

    // Get tenant-specific connection from context
    db, err := tenantmanager.GetPostgresForTenant(ctx)
    if err != nil {
        libOpentelemetry.HandleSpanError(&span, "Failed to get database connection", err)
        logger.Errorf("Failed to get database connection: %v", err)
        return nil, err
    }

    record := &EntityPostgreSQLModel{}
    record.FromEntity(entity)

    // Use db for queries - automatically scoped to tenant's database
    // ...
}
```

### Redis Key Prefixing

```go
// internal/adapters/redis/repository.go
func (r *RedisRepository) Set(ctx context.Context, key, value string, ttl time.Duration) error {
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "redis.set")
    defer span.End()

    // Tenant-aware key prefixing (adds tenant:{tenantId}: prefix if multi-tenant)
    key = tenantmanager.GetKeyFromContext(ctx, key)

    rds, err := r.conn.GetClient(ctx)
    if err != nil {
        return err
    }

    return rds.Set(ctx, key, value, ttl).Err()
}
```

### RabbitMQ Multi-Tenant Producer

```go
// internal/adapters/rabbitmq/producer.go
type ProducerRepository struct {
    conn            *libRabbitmq.RabbitMQConnection
    rabbitMQManager *tenantmanager.RabbitMQManager
    multiTenantMode bool
}

// Single-tenant constructor
func NewProducer(conn *libRabbitmq.RabbitMQConnection) *ProducerRepository {
    return &ProducerRepository{
        conn:            conn,
        multiTenantMode: false,
    }
}

// Multi-tenant constructor
func NewProducerMultiTenant(pool *tenantmanager.RabbitMQManager) *ProducerRepository {
    return &ProducerRepository{
        rabbitMQManager: pool,
        multiTenantMode: true,
    }
}

func (p *ProducerRepository) Publish(ctx context.Context, exchange, key string, message []byte) error {
    // Inject tenant ID header
    tenantID := tenantmanager.GetTenantID(ctx)
    headers := amqp.Table{}
    if tenantID != "" {
        headers["X-Tenant-ID"] = tenantID
    }

    if p.multiTenantMode {
        if tenantID == "" {
            return fmt.Errorf("tenant ID is required in multi-tenant mode")
        }

        // Get tenant-specific channel from pool
        channel, err := p.rabbitMQManager.GetChannel(ctx, tenantID)
        if err != nil {
            return err
        }

        return channel.PublishWithContext(ctx, exchange, key, false, false,
            amqp.Publishing{
                ContentType:  "application/json",
                DeliveryMode: amqp.Persistent,
                Headers:      headers,
                Body:         message,
            })
    }

    // Single-tenant: use static connection
    return p.conn.Channel.Publish(exchange, key, false, false,
        amqp.Publishing{Body: message, Headers: headers})
}
```

### MongoDB Multi-Tenant Repository

```go
// internal/adapters/mongodb/metadata.go
type MetadataMongoDBRepository struct {
    conn *libMongo.MongoConnection // Single-tenant
}

func NewMetadataMongoDBRepository(conn *libMongo.MongoConnection) *MetadataMongoDBRepository {
    return &MetadataMongoDBRepository{conn: conn}
}

func (r *MetadataMongoDBRepository) Create(ctx context.Context, collection string, metadata *Metadata) error {
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "mongodb.create_metadata")
    defer span.End()

    // Get tenant-specific database from context
    tenantDB, err := tenantmanager.GetMongoForTenant(ctx)
    if err != nil {
        libOpentelemetry.HandleSpanError(&span, "Failed to get database connection", err)
        return err
    }

    // Use tenant's database for operations
    coll := tenantDB.Collection(strings.ToLower(collection))

    record := &MetadataMongoDBModel{}
    if err := record.FromEntity(metadata); err != nil {
        return err
    }

    _, err = coll.InsertOne(ctx, record)
    if err != nil {
        libOpentelemetry.HandleSpanError(&span, "Failed to insert metadata", err)
        return err
    }

    return nil
}
```

### Conditional Initialization

```go
// internal/bootstrap/service.go
func InitService(cfg *Config) (*Service, error) {
    if cfg.MultiTenantEnabled && cfg.MultiTenantURL != "" {
        // Create client, managers, and middleware (as shown in Generic TenantMiddleware above)
        // ...
        logger.Infof("Multi-tenant mode enabled with Tenant Manager URL: %s", cfg.MultiTenantURL)
    } else {
        logger.Info("Running in SINGLE-TENANT MODE")
    }

    // Continue with normal service initialization
    // ...
}
```

### Testing Multi-Tenant Code

#### Unit Tests with Mock Tenant Context

```go
// internal/service/user_service_test.go
func TestUserService_Create_WithTenantContext(t *testing.T) {
    // Setup tenant context
    tenantID := "tenant-123"
    ctx := tenantmanager.ContextWithTenantID(context.Background(), tenantID)

    // Mock database connection
    mockDB := setupMockDB(t)
    ctx = tenantmanager.ContextWithTenantPGConnection(ctx, mockDB)

    // Create service with mock dependencies
    repo := repository.NewUserRepository()
    service := service.NewUserService(repo, logger)

    // Execute
    input := &CreateUserInput{Name: "John", Email: "john@example.com"}
    result, err := service.Create(ctx, input)

    // Assert
    require.NoError(t, err)
    assert.Equal(t, "John", result.Name)
}
```

#### Testing Tenant Isolation

```go
func TestRepository_Create_TenantIsolation(t *testing.T) {
    tests := []struct {
        name     string
        tenantID string
        input    *Entity
        wantErr  bool
    }{
        {
            name:     "tenant-1 creates entity",
            tenantID: "tenant-1",
            input:    &Entity{Name: "Entity A"},
            wantErr:  false,
        },
        {
            name:     "tenant-2 creates same entity (isolated)",
            tenantID: "tenant-2",
            input:    &Entity{Name: "Entity A"},
            wantErr:  false, // Different tenant = different database = allowed
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Inject tenant-specific context
            ctx := tenantmanager.ContextWithTenantID(context.Background(), tt.tenantID)
            ctx = tenantmanager.ContextWithTenantPGConnection(ctx, mockDB)

            _, err := repo.Create(ctx, tt.input)

            if tt.wantErr {
                require.Error(t, err)
            } else {
                require.NoError(t, err)
            }
        })
    }
}
```

#### Integration Tests with Tenant Isolation

```go
// tests/integration/multi_tenant_test.go
func TestMultiTenant_TenantIsolation(t *testing.T) {
    if !h.IsMultiTenantEnabled() {
        t.Skip("Multi-tenant mode is not enabled")
    }

    env := h.LoadEnvironment()
    ctx := context.Background()
    client := h.NewHTTPClient(env.ServerURL, env.HTTPTimeout)

    // Define two distinct tenants
    tenantA := "tenant-a-" + h.RandString(6)
    tenantB := "tenant-b-" + h.RandString(6)

    headersTenantA := h.TenantAuthHeaders(h.RandHex(8), tenantA)
    headersTenantB := h.TenantAuthHeaders(h.RandHex(8), tenantB)

    // Step 1: Tenant A creates organization
    codeA, bodyA, _ := client.Request(ctx, "POST", "/v1/organizations", headersTenantA, orgPayload)
    require.Equal(t, 201, codeA)

    var orgA struct{ ID string `json:"id"` }
    json.Unmarshal(bodyA, &orgA)

    // Step 2: Tenant B creates organization
    codeB, bodyB, _ := client.Request(ctx, "POST", "/v1/organizations", headersTenantB, orgPayload)
    require.Equal(t, 201, codeB)

    var orgB struct{ ID string `json:"id"` }
    json.Unmarshal(bodyB, &orgB)

    // Step 3: Verify Tenant A cannot see Tenant B's data
    code, body, _ := client.Request(ctx, "GET", "/v1/organizations", headersTenantA, nil)
    require.Equal(t, 200, code)

    var list struct{ Items []struct{ ID string `json:"id"` } `json:"items"` }
    json.Unmarshal(body, &list)

    for _, item := range list.Items {
        assert.NotEqual(t, orgB.ID, item.ID, "ISOLATION VIOLATION: Tenant A can see Tenant B's data")
    }
}
```

#### Testing Error Cases

```go
func TestMiddleware_WithTenantDB_ErrorCases(t *testing.T) {
    tests := []struct {
        name           string
        setupContext   func(*fiber.Ctx)
        expectedStatus int
        expectedCode   string
    }{
        {
            name: "missing JWT token",
            setupContext: func(c *fiber.Ctx) {
                // No Authorization header
            },
            expectedStatus: 401,
            expectedCode:   "TENANT_ID_REQUIRED",
        },
        {
            name: "JWT without tenantId claim",
            setupContext: func(c *fiber.Ctx) {
                token := createJWTWithoutTenantClaim()
                c.Request().Header.Set("Authorization", "Bearer "+token)
            },
            expectedStatus: 401,
            expectedCode:   "TENANT_ID_REQUIRED",
        },
        {
            name: "tenant not found in Tenant Manager",
            setupContext: func(c *fiber.Ctx) {
                token := createJWT(map[string]interface{}{"tenantId": "unknown-tenant"})
                c.Request().Header.Set("Authorization", "Bearer "+token)
            },
            expectedStatus: 404,
            expectedCode:   "TENANT_NOT_FOUND",
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            app := fiber.New()
            ctx := app.AcquireCtx(&fasthttp.RequestCtx{})
            defer app.ReleaseCtx(ctx)

            tt.setupContext(ctx)

            err := middleware.WithTenantDB(ctx)

            require.Error(t, err)
            fiberErr, ok := err.(*fiber.Error)
            require.True(t, ok)
            assert.Equal(t, tt.expectedStatus, fiberErr.Code)
        })
    }
}
```

#### Testing RabbitMQ Multi-Tenant Consumer

```go
func TestRabbitMQConsumer_MultiTenant(t *testing.T) {
    t.Run("injects tenant context from X-Tenant-ID header", func(t *testing.T) {
        tenantID := "tenant-456"

        // Create message with tenant header
        message := amqp.Delivery{
            Headers: amqp.Table{
                "X-Tenant-ID": tenantID,
            },
            Body: []byte(`{"action": "create"}`),
        }

        // Setup consumer
        consumer := NewMultiTenantConsumer(pool, logger)

        // Process message
        ctx, err := consumer.injectTenantDBConnections(
            context.Background(),
            tenantID,
            logger,
        )

        // Assert tenant context injected
        require.NoError(t, err)
        extractedTenant := tenantmanager.GetTenantID(ctx)
        assert.Equal(t, tenantID, extractedTenant)
    })
}
```

#### Testing Redis Key Prefixing

```go
func TestRedisRepository_MultiTenant_KeyPrefixing(t *testing.T) {
    t.Run("prefixes keys with tenant ID", func(t *testing.T) {
        tenantID := "tenant-789"
        ctx := tenantmanager.ContextWithTenantID(context.Background(), tenantID)

        repo := NewRedisRepository(redisConn)

        err := repo.Set(ctx, "user:session", "value123", 3600)
        require.NoError(t, err)

        // Verify key was prefixed
        key := tenantmanager.GetKeyFromContext(ctx, "user:session")
        assert.Equal(t, "tenant:tenant-789:user:session", key)
    })

    t.Run("single-tenant mode does not prefix keys", func(t *testing.T) {
        ctx := context.Background()

        key := tenantmanager.GetKeyFromContext(ctx, "user:session")
        assert.Equal(t, "user:session", key)
    })
}
```

### Error Handling

| Error | HTTP Status | Code | When |
|-------|-------------|------|------|
| Missing tenantId claim | 401 | `TENANT_ID_REQUIRED` | JWT doesn't have tenantId |
| Tenant not found | 404 | `TENANT_NOT_FOUND` | Tenant not registered in Tenant Manager |
| Tenant not provisioned | 422 | `TENANT_NOT_PROVISIONED` | Database schema not initialized (SQLSTATE 42P01) |
| Tenant suspended | 403 | service-specific | Tenant status is suspended or purged (use `errors.As(err, &TenantSuspendedError{})`) |
| Service not configured | 503 | service-specific | Tenant exists but has no config for this service/module (`ErrServiceNotConfigured`) |
| Schema mode error | 422 | service-specific | Invalid schema configuration for tenant database |
| Connection error | 503 | service-specific | Failed to get or establish tenant connection |
| Manager closed | 503 | service-specific | Connection manager has been shut down (`ErrManagerClosed`) |
| Circuit breaker open | 503 | service-specific | Tenant Manager client tripped after consecutive failures (`ErrCircuitBreakerOpen`) |
| Tenant config rate limited | 503 | service-specific | Too many concurrent requests for the same tenant config — retry after brief delay |

### Tenant Isolation Verification (⚠️ CONDITIONAL)

Multi-tenant applications MUST verify tenant isolation to prevent data leakage between tenants.

**⛔ CONDITIONAL:** This section applies ONLY if `MULTI_TENANT_ENABLED=true`. If single-tenant, mark as N/A.

**Detection Question:** Is this a multi-tenant service?

```bash
# Check if multi-tenant mode is enabled
grep -rn "MULTI_TENANT_ENABLED\|MultiTenantEnabled" internal/ --include="*.go"

# If 0 matches OR always set to false: Mark N/A
# If found AND can be true: Apply this section
```

#### Isolation Architecture

Multi-tenant isolation uses a **database-per-tenant** model with two isolation layers:

| Layer | Mechanism | Protection |
|-------|-----------|------------|
| **Primary: Database isolation** | `TenantConnectionManager` returns separate database per tenant | Tenant A cannot query Tenant B's database |
| **Secondary: Entity scoping** | `organization_id` + `ledger_id` in WHERE clauses | Intra-tenant entity separation |

#### Why Tenant Isolation Verification Is MANDATORY

| Attack | Without Verification | With Verification |
|--------|----------------------|-------------------|
| Cross-tenant data access | Tenant A accesses Tenant B's database | Connection-level isolation prevents it |
| Data exfiltration | Cross-tenant data leakage | Separate databases per tenant |
| IDOR within tenant | User accesses wrong organization's data | `organization_id` in WHERE clause |

#### Entity Scoping Pattern (REQUIRED)

Within each tenant's database, queries MUST scope by `organization_id` and `ledger_id`:

```go
// internal/adapters/postgres/entity/entity.postgresql.go
func (r *EntityPostgreSQLRepository) Find(ctx context.Context, organizationID, ledgerID, id uuid.UUID) (*Entity, error) {
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "postgres.find_entity")
    defer span.End()

    db, err := tenantmanager.GetPostgresForTenant(ctx)
    if err != nil {
        return nil, err
    }

    // Query scoped by organization_id and ledger_id
    find := squirrel.Select(entityColumnList...).
        From(r.tableName).
        Where(squirrel.Expr("organization_id = ?", organizationID)).
        Where(squirrel.Expr("ledger_id = ?", ledgerID)).
        Where(squirrel.Expr("id = ?", id)).
        Where(squirrel.Eq{"deleted_at": nil}).
        PlaceholderFormat(squirrel.Dollar)

    query, args, err := find.ToSql()
    if err != nil {
        return nil, err
    }

    row := db.QueryRowContext(ctx, query, args...)
    // ...
}
```

#### FORBIDDEN Patterns

```go
// ❌ FORBIDDEN: Query without entity scoping
query := `SELECT * FROM entities WHERE id = $1`  // WRONG: No organization_id/ledger_id
row := db.QueryRowContext(ctx, query, id)

// ❌ FORBIDDEN: Missing ledger_id in query
query := `SELECT * FROM entities WHERE organization_id = $1 AND id = $2`  // WRONG: No ledger_id

// ❌ FORBIDDEN: Post-query entity check
entity, err := r.GetByID(ctx, id)
if entity.OrganizationID != organizationID {  // WRONG: Data already fetched
    return nil, ErrForbidden
}
// ✅ CORRECT: Filter in WHERE clause, return ErrNotFound
```

#### Detection Commands (MANDATORY)

```bash
# MANDATORY: Run before every PR in multi-tenant services
# Find queries without organization_id in WHERE clause
grep -rn "SELECT.*FROM.*WHERE" internal/adapters/postgres --include="*.go" | \
  grep -v "organization_id" | grep -v "_test.go"

# Find SELECTs that may lack WHERE
grep -rn "SELECT.*FROM" internal/adapters/postgres --include="*.go" | grep -v "WHERE" | grep -v "_test.go"

# Capture multi-line SQL: call sites that may split queries across lines
grep -rn "QueryRowContext\|QueryContext" internal/ --include="*.go" | grep -v "_test.go"

# Find post-query entity checks (potential information leak)
grep -rn "OrganizationID.*!=\|\.OrganizationID\s*==" internal/ --include="*.go" | grep -v "_test.go"

# Expected: All queries should include organization_id (or have documented exception)
```

#### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Database is per-tenant anyway" | Database-per-tenant prevents cross-tenant but not intra-tenant IDOR. | **Add organization_id to all queries** |
| "Only admins access this endpoint" | Admins can access wrong organization. Verify anyway. | **Add organization_id to all queries** |
| "Post-query check is the same" | Post-query reveals data was fetched. Information leak. | **Filter in WHERE clause** |
| "We trust authenticated users" | Authentication != Authorization. Entity scope is authorization. | **Add organization_id to all queries** |
| "It's just metadata" | Metadata can reveal business information. | **Add organization_id to all queries** |

### Context Functions

lib-commons provides two sets of context functions. They use **separate, isolated context keys** with no fallback between them.

| Function | Context Key | Use When |
|----------|-------------|----------|
| `GetPostgresForTenant(ctx)` | `tenantPGConnection` | Standard — one database per tenant |
| `GetModulePostgresForTenant(ctx, module)` | `tenantPGConnection:{module}` | When service has multiple database modules |

```go
// Standard usage
db, err := tenantmanager.GetPostgresForTenant(ctx)
if err != nil {
    // ErrTenantContextRequired: middleware not set up or tenant not resolved
    return err
}

// If service has multiple database modules
db, err := tenantmanager.GetModulePostgresForTenant(ctx, "my-module")
```

**Context setters (used by middleware, not by service code):**
- `ContextWithTenantID(ctx, tenantID)` — stores tenant ID
- `ContextWithTenantPGConnection(ctx, db)` — generic PG connection (set by TenantMiddleware)
- `ContextWithModulePGConnection(ctx, module, db)` — module-specific PG (when service has multiple DB modules)
- `ContextWithTenantMongo(ctx, mongoDB)` — MongoDB connection

### Tenant ID Validation

lib-commons validates tenant IDs to prevent path traversal and injection:

```go
const maxTenantIDLength = 256
var validTenantIDPattern = regexp.MustCompile(`^[a-zA-Z0-9][a-zA-Z0-9_-]*$`)
```

Rules:
- Must start with alphanumeric character
- Only alphanumeric, underscore, and hyphen allowed
- Maximum 256 characters
- Empty strings rejected

### Redis Key Prefixing for Lua Scripts

Beyond simple `Set/Get` operations, Redis Lua scripts require special attention. ALL keys passed as `KEYS[]` and `ARGV[]` to Lua scripts MUST be pre-prefixed in Go **before** the script execution:

```go
// ✅ CORRECT: Prefix keys in Go before Lua execution
prefixedBackupQueue := tenantmanager.GetKeyFromContext(ctx, TransactionBackupQueue)
prefixedTransactionKey := tenantmanager.GetKeyFromContext(ctx, transactionKey)
prefixedBalanceSyncKey := tenantmanager.GetKeyFromContext(ctx, utils.BalanceSyncScheduleKey)

// Also prefix ARGV values that are used as keys inside the Lua script
prefixedInternalKey := tenantmanager.GetKeyFromContext(ctx, blcs.InternalKey)

result, err := script.Run(ctx, rds,
    []string{prefixedBackupQueue, prefixedTransactionKey, prefixedBalanceSyncKey},
    finalArgs...).Result()
```

```go
// ❌ FORBIDDEN: Hardcoded keys inside Lua script
-- Lua script must NEVER reference keys by name
local key = "balance:lock"  -- WRONG: not tenant-prefixed

// ✅ CORRECT: Lua script uses only KEYS[] and ARGV[]
local backupQueue = KEYS[1]  -- Already prefixed by Go caller
local txKey = KEYS[2]        -- Already prefixed by Go caller
```

This pattern also ensures Redis Cluster compatibility (all keys in `KEYS[]` must be in the same hash slot for atomic operations).

### Multi-Tenant Metrics

Services implementing multi-tenant MUST expose these metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `tenant_connections_total` | Counter | Total tenant connections created |
| `tenant_connection_errors_total` | Counter | Connection failures per tenant |
| `tenant_consumers_active` | Gauge | Active message consumers |
| `tenant_messages_processed_total` | Counter | Messages processed per tenant |

### Responsibility Split: lib-commons vs Service

| Responsibility | lib-commons handles | Service MUST implement |
|---------------|--------------------|-----------------------|
| **Connection pooling** | Cache per tenant, double-check locking | - |
| **Credential fetching** | HTTP call to Tenant Manager API | - |
| **JWT parsing** | Extract `tenantId` from token (middleware) | - |
| **Tenant discovery** | Redis -> API fallback, sync loop | - |
| **Lazy consumer lifecycle** | On-demand spawn, backoff, degraded tracking | - |
| **Middleware registration** | - | Register `TenantMiddleware` on routes |
| **Repository adaptation** | - | Use `GetPostgresForTenant(ctx)` instead of global DB |
| **Redis key prefixing** | - | Call `GetKeyFromContext(ctx, key)` for every Redis operation |
| **Consumer setup** | - | Register handlers, call `consumer.Run(ctx)` at startup |
| **Consumer trigger** | - | Call `EnsureConsumerStarted(ctx, tenantID)` from middleware |
| **Error handling** | Return sentinel errors | Map errors to HTTP status codes |

### ConsumerTrigger Interface

Services that process messages in multi-tenant mode MUST implement the `ConsumerTrigger` interface and wire it into the middleware for lazy consumer activation:

```go
// pkg/mbootstrap/interfaces.go
type ConsumerTrigger interface {
    EnsureConsumerStarted(ctx context.Context, tenantID string)
}
```

The middleware calls `EnsureConsumerStarted` after extracting the tenant ID. First request per tenant spawns the consumer (~500ms). Subsequent requests return immediately (<1ms).

### Anti-Rationalization Table (General)

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "We only have one customer" | Requirements change. Multi-tenant is easy to add now, hard later. | **Design for multi-tenant, deploy as single** |
| "Tenant Manager adds complexity" | Complexity is in connection management anyway. Tenant Manager standardizes it. | **Use Tenant Manager for multi-tenant** |
| "JWT parsing is expensive" | Parse once in middleware, use from context everywhere. | **Extract tenant once, propagate via context** |
| "We'll add tenant isolation later" | Retrofitting tenant isolation is a rewrite. | **Build tenant-aware from the start** |

### Final Step: Single-Tenant Backward Compatibility Validation (MANDATORY)

**HARD GATE: This is the LAST step of every multi-tenant implementation.** CANNOT merge or deploy without completing this validation.

If the service was already running as single-tenant before multi-tenant was added, it MUST continue working unchanged with `MULTI_TENANT_ENABLED=false` (the default). Multi-tenant is opt-in. Single-tenant is the baseline. Breaking it is a production incident for all existing deployments.

#### How the Backward Compatibility Mechanism Works

The middleware checks `pool.IsMultiTenant()` at the start of every request. When `MULTI_TENANT_ENABLED=false`:
- `IsMultiTenant()` returns `false`
- Middleware returns `c.Next()` immediately — zero tenant logic applied
- No JWT parsing, no Tenant Manager calls, no pool routing
- The service uses its default database connection as before

```go
// Single-tenant mode: pass through if pool is not multi-tenant
if !pool.IsMultiTenant() {
    return c.Next()  // No tenant logic applied — service works as before
}
```

#### Validation Steps (execute in order)

**Step 1 — Remove all multi-tenant env vars and start the service:**
```bash
# Unset ALL multi-tenant variables
unset MULTI_TENANT_ENABLED MULTI_TENANT_URL MULTI_TENANT_ENVIRONMENT
unset MULTI_TENANT_MAX_TENANT_POOLS MULTI_TENANT_IDLE_TIMEOUT_SEC
unset MULTI_TENANT_CIRCUIT_BREAKER_THRESHOLD MULTI_TENANT_CIRCUIT_BREAKER_TIMEOUT_SEC

# Start the service — MUST start without errors, without Tenant Manager running
go run cmd/app/main.go
# Expected log: "Running in SINGLE-TENANT MODE"
```

**Step 2 — Run the full existing test suite (single-tenant):**
```bash
# ALL pre-existing tests MUST pass with multi-tenant disabled
MULTI_TENANT_ENABLED=false go test ./...
```

**Step 3 — Run backward compatibility integration test:**
```go
func TestMultiTenant_BackwardCompatibility(t *testing.T) {
    // MUST skip when multi-tenant is enabled — this test validates single-tenant only
    if h.IsMultiTenantEnabled() {
        t.Skip("Skipping backward compatibility test - multi-tenant mode is enabled")
    }

    // Create resources WITHOUT tenant context — MUST work in single-tenant mode
    code, body, err := client.Request(ctx, "POST", "/v1/organizations", headers, orgPayload)
    require.Equal(t, 201, code, "single-tenant CRUD must work without tenant context")

    // List resources — MUST return data normally
    code, body, err = client.Request(ctx, "GET", "/v1/organizations", headers, nil)
    require.Equal(t, 200, code, "single-tenant list must work without tenant context")

    // Health endpoints — MUST work without any auth or tenant context
    code, _, _ = client.Request(ctx, "GET", "/health", nil, nil)
    require.Equal(t, 200, code, "health endpoint must work in single-tenant mode")
}
```

**Step 4 — Validate against this checklist:**

| # | Check | How to Verify | Pass Criteria |
|---|-------|--------------|---------------|
| 1 | Service starts without `MULTI_TENANT_*` vars | Remove all vars, start service | Starts normally, logs "SINGLE-TENANT MODE" |
| 2 | Service starts without Tenant Manager | Don't run Tenant Manager, start service | No connection errors, no panics |
| 3 | All existing CRUD operations work | Run pre-existing integration tests | All pass with same behavior as before |
| 4 | Health/version/swagger endpoints work | `GET /health`, `GET /version` | 200 OK without any auth headers |
| 5 | Default DB connection is used | Check DB queries go to the configured `DB_HOST` | Queries hit single-tenant database |
| 6 | No new required env vars break startup | Start with only the env vars the service had before | Service starts without errors |

**Step 5 — Run multi-tenant test suite (both modes work):**
```bash
# Confirm multi-tenant mode also works
MULTI_TENANT_ENABLED=true MULTI_TENANT_URL=http://tenant-manager:4003 go test ./... -run "MultiTenant"
```

#### Anti-Rationalization

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Nobody uses single-tenant anymore" | Existing deployments depend on it. Breaking them is a production incident for every customer running self-hosted. | **STOP. Run the validation steps.** |
| "We tested multi-tenant, that's enough" | Multi-tenant tests exercise a DIFFERENT code path (`IsMultiTenant()=true`). Single-tenant (`IsMultiTenant()=false`) is a separate path that needs separate verification. | **STOP. Run both test suites.** |
| "The passthrough is trivial, it can't break" | Config struct changes, new required env vars, middleware ordering changes, import side effects — all of these can silently break the passthrough path. | **STOP. Verify with actual requests.** |
| "I'll test single-tenant later" | Later never comes. Once merged, the damage is done. Existing CI may not catch it if tests assume multi-tenant. | **STOP. Test now, before merge.** |

### Checklist

**Environment Variables:**
- [ ] `MULTI_TENANT_ENABLED` in config struct (default: `false`)
- [ ] `MULTI_TENANT_URL` in config struct (required if multi-tenant)
- [ ] `MULTI_TENANT_ENVIRONMENT` in config struct (default: `staging`)
- [ ] `MULTI_TENANT_MAX_TENANT_POOLS` in config struct (default: `100`)
- [ ] `MULTI_TENANT_IDLE_TIMEOUT_SEC` in config struct (default: `300`)
- [ ] `MULTI_TENANT_CIRCUIT_BREAKER_THRESHOLD` in config struct (default: `5`)
- [ ] `MULTI_TENANT_CIRCUIT_BREAKER_TIMEOUT_SEC` in config struct (default: `30`)

**Architecture:**
- [ ] `tenantmanager.NewClient(url, logger)` for Tenant Manager HTTP client
- [ ] `tenantmanager.NewPostgresManager(client, service, WithModule(...), WithPostgresLogger(...), WithMaxTenantPools(...), WithIdleTimeout(...))` for PostgreSQL pool
- [ ] `tenantmanager.NewTenantMiddleware(WithPostgresManager(...))` for middleware
- [ ] `tenantmanager.GetPostgresForTenant(ctx)` in repositories

**Middleware & Context:**
- [ ] JWT tenant extraction (claim key: `tenantId`)
- [ ] `tenantmanager.ContextWithTenantID()` in middleware
- [ ] Public endpoints (`/health`, `/version`, `/swagger`) bypass tenant middleware
- [ ] `ErrTenantNotFound` → 404, `ErrManagerClosed` → 503, `ErrServiceNotConfigured` → 503
- [ ] `IsTenantNotProvisionedError()` in error handler → 422
- [ ] `ErrTenantContextRequired` handled in repositories
- [ ] `ConsumerTrigger.EnsureConsumerStarted()` called after tenant ID extraction (if using lazy mode)

**Repositories:**
- [ ] `tenantmanager.GetPostgresForTenant(ctx)` in PostgreSQL repositories
- [ ] `tenantmanager.GetKeyFromContext(ctx, key)` for ALL Redis keys (including Lua script KEYS[] and ARGV[])
- [ ] `tenantmanager.GetMongoForTenant(ctx)` in MongoDB repositories (if using MongoDB)

**Async Processing:**
- [ ] Tenant ID header (`X-Tenant-ID`) in RabbitMQ messages
- [ ] `NewMultiTenantConsumer` with `WithConsumerPostgresManager` and `WithConsumerMongoManager`
- [ ] `consumer.Register(queueName, handler)` for each queue
- [ ] `consumer.Run(ctx)` at startup (non-blocking, <1s)
- [ ] `ConsumerTrigger` interface implemented and wired to middleware

**Testing:**
- [ ] Unit tests with mock tenant context
- [ ] Tenant isolation tests (verify data separation between tenants)
- [ ] Error case tests (missing tenant, invalid tenant, tenant not found)
- [ ] Integration tests with two distinct tenants verifying cross-tenant isolation
- [ ] RabbitMQ consumer tests (X-Tenant-ID header extraction)
- [ ] Redis key prefixing tests (verify tenant prefix applied, including Lua scripts)

**Single-Tenant Backward Compatibility (MANDATORY):**
- [ ] All existing tests pass with `MULTI_TENANT_ENABLED=false` (default)
- [ ] Service starts without any `MULTI_TENANT_*` environment variables
- [ ] Service starts without Tenant Manager running
- [ ] All CRUD operations work in single-tenant mode
- [ ] Backward compatibility integration test exists (`TestMultiTenant_BackwardCompatibility`)
- [ ] Health/version endpoints work without tenant context

---

## Multi-Tenant Message Queue Consumers (Lazy Mode)

### When to Use

**CONDITIONAL:** Only applies if your service:
- Processes messages from a message broker (RabbitMQ, SQS, etc.)
- Uses per-tenant message isolation (dedicated vhosts or queues per tenant)
- Has 10+ tenants where startup time is a concern

**If single-tenant or <10 tenants:** Multi-tenant mode overhead may be unnecessary. Consider single-tenant architecture.

---

### Problem: Startup Time Scales with Tenant Count

In multi-tenant services consuming messages, connecting to ALL tenant vhosts at startup causes:

```
Startup Time = N tenants × 500ms per connection
10 tenants  = 5 seconds
100 tenants = 50 seconds  ← Unacceptable for autoscaling/deployments
```

**Symptoms:**
- Slow deployments (rolling updates wait for each pod to connect)
- Poor autoscaling responsiveness (new pods take 30-60s to become ready)
- Wasted resources (connections to inactive tenants)

---

### Solution: Lazy Consumer Initialization

**Pattern:** Decouple tenant discovery from consumer connection.

```
Startup:
  1. Discover tenant list (Redis/API) - lightweight, <1s
  2. Track discovered tenants in memory (knownTenants map)
  3. Do NOT start consumers yet
  4. Return immediately (startup complete)

On First Request per Tenant:
  1. HTTP middleware extracts tenant ID
  2. Middleware calls consumer.EnsureConsumerStarted(ctx, tenantID)
  3. Consumer spawns on-demand (first time: ~500ms)
  4. Connection cached for reuse
  5. Subsequent requests: fast path (<1ms)
```

**Result:** Startup time O(1) regardless of tenant count, resources scale with active tenants only.

---

### Architecture Components

#### 1. Tenant Discovery Service

**Responsibility:** Provide list of active tenants without connection overhead.

**Implementation:**
- **Primary:** Cache (Redis SET: `tenant-manager:tenants:active`)
- **Fallback:** HTTP API (`GET /tenants/active?service={serviceName}`)

**Response format (API):**
```json
[
  {"id": "tenant-001", "name": "Tenant A", "status": "active"},
  {"id": "tenant-002", "name": "Tenant B", "status": "active"}
]
```

**Endpoint characteristics:**
- Returns minimal info (id, name, status only)
- Supports optional filtering by service (query param: `?service={serviceName}`)

#### 2. Consumer Manager (lib-commons)

**Responsibility:** Manage lifecycle of message consumers across tenants with lazy initialization.

**Key methods:**
```go
type MultiTenantConsumer struct {
    mu sync.RWMutex                      // Protects knownTenants and activeTenants maps
    knownTenants map[string]bool        // Discovered tenants
    activeTenants map[string]CancelFunc // Running consumers
    consumerLocks sync.Map               // Per-tenant mutexes
    retryState sync.Map                  // Failure tracking
}

// Discover tenants without connecting (non-blocking, <1s)
func (c *MultiTenantConsumer) Run(ctx context.Context) error

// Ensure consumer is active for tenant (idempotent, thread-safe, fire-and-forget)
func (c *MultiTenantConsumer) EnsureConsumerStarted(ctx context.Context, tenantID string)

// Check if tenant has failed repeatedly
func (c *MultiTenantConsumer) IsDegraded(tenantID string) bool

// Get runtime statistics
func (c *MultiTenantConsumer) Stats() ConsumerStats
```

#### 3. HTTP Middleware Trigger

**Responsibility:** Trigger lazy consumer spawn when requests arrive.

**Implementation pattern:**
```go
func TenantMiddleware(consumer ConsumerTrigger) fiber.Handler {
    return func(c *fiber.Ctx) error {
        // Extract tenant ID from header or JWT
        tenantID := c.Get("x-tenant-id")
        if tenantID == "" {
            return fiber.NewError(400, "x-tenant-id required")
        }

        // Lazy mode trigger: ensure consumer is active
        // First time: spawns consumer (~500ms)
        // Subsequent: fast path (<1ms)
        if consumer != nil {  // Nil-safe for single-tenant mode
            ctx := c.UserContext()
            consumer.EnsureConsumerStarted(ctx, tenantID)
            // Fire-and-forget: consumer retries via background sync if spawn fails
        }

        // Continue with request processing
        return c.Next()
    }
}
```

**Placement:** After tenant ID extraction, before database connection resolution.

---

### Implementation Steps

#### Step 1: Update Shared Library

Implement lazy mode in your message queue consumer library:

1. **Add state tracking:**
```go
knownTenants map[string]bool        // Discovered via API/cache
activeTenants map[string]CancelFunc // Actually running
consumerLocks sync.Map               // Prevent duplicate spawns
```

2. **Non-blocking discovery:**
```go
func (c *Consumer) Run(ctx context.Context) error {
    // Discover tenants (timeout: 500ms, soft failure)
    c.discoverTenants(ctx)

    // Start background sync loop (for tenant add/remove)
    go c.runSyncLoop(ctx)

    return nil  // Return immediately
}
```

3. **On-demand spawning with double-check locking:**
```go
func (c *Consumer) EnsureConsumerStarted(ctx context.Context, tenantID string) {
    // Fast path: check if already active (read lock)
    c.mu.RLock()
    if _, exists := c.activeTenants[tenantID]; exists {
        c.mu.RUnlock()
        return  // Already running
    }
    c.mu.RUnlock()

    // Slow path: acquire per-tenant mutex (prevent thundering herd)
    mutex := c.getPerTenantMutex(tenantID)
    mutex.Lock()
    defer mutex.Unlock()

    // Double-check after acquiring lock
    c.mu.RLock()
    if _, exists := c.activeTenants[tenantID]; exists {
        c.mu.RUnlock()
        return  // Another goroutine created it
    }
    c.mu.RUnlock()

    // Spawn consumer (fire-and-forget, errors logged internally)
    c.startTenantConsumer(ctx, tenantID)
}
```

#### Step 2: Add Tenant Discovery Endpoint

In your tenant management service:

```go
// GET /tenants/active?service={serviceName}
func GetActiveTenants(c *fiber.Ctx) error {
    service := c.Query("service")

    // Query active tenants (filter by service if provided)
    tenants, err := repo.ListActiveTenants(service)
    if err != nil {
        return libHTTP.InternalServerError(c, "TENANT_LIST_FAILED", err)
    }

    // Return minimal info (no credentials)
    response := []TenantSummary{}
    for _, t := range tenants {
        response = append(response, TenantSummary{
            ID: t.ID,
            Name: t.Name,
            Status: t.Status,
        })
    }

    return libHTTP.OK(c, response)
}

// Register as PUBLIC endpoint (no auth)
app.Get("/tenants/active", GetActiveTenants)
```

#### Step 3: Wire Trigger in Service Middleware

In each service consuming messages:

```go
// In bootstrap/config.go
func InitServers() {
    // Create multi-tenant consumer
    consumer := tenantmanager.NewMultiTenantConsumer(...)
    if err := consumer.Run(ctx); err != nil {
        logger.Errorf("tenant manager startup failed: %v", err)
        // Note: startup continues - consumer will retry tenant discovery in background
    }

    // Create middleware with consumer trigger
    tenantMiddleware := NewTenantMiddleware(consumer)

    // Register middleware
    app.Use(tenantMiddleware)
}

// In middleware file
type TenantMiddleware struct {
    consumer ConsumerTrigger  // Interface with EnsureConsumerStarted method
}

func (m *TenantMiddleware) Handle(c *fiber.Ctx) error {
    tenantID := extractTenantID(c)  // From header or JWT

    // Lazy mode trigger (fire-and-forget, errors logged internally)
    if m.consumer != nil {
        ctx := c.UserContext()
        m.consumer.EnsureConsumerStarted(ctx, tenantID)
    }

    return c.Next()
}
```

---

### Failure Resilience Pattern

**Exponential Backoff:**
```go
func backoffDelay(retryCount int) time.Duration {
    delays := []time.Duration{5*time.Second, 10*time.Second, 20*time.Second, 40*time.Second}
    if retryCount >= len(delays) {
        return delays[len(delays)-1]  // Cap at 40s
    }
    return delays[retryCount]
}
```

**Per-Tenant Retry State:**
```go
type retryState struct {
    count    int
    degraded bool  // True after 3 failures
}

retryState sync.Map  // Key: tenantID, Value: *retryState
```

**Degraded Tenant Handling:**
```go
if consumer.IsDegraded(tenantID) {
    logger.Errorf("Tenant %s is degraded (3+ connection failures)", tenantID)
    return errors.New("tenant degraded")
}
```

---

### Observability Pattern

**Enhanced Stats API:**
```go
type ConsumerStats struct {
    ConnectionMode   string   `json:"connectionMode"`    // "lazy"
    ActiveTenants    int      `json:"activeTenants"`     // Connected
    KnownTenants     int      `json:"knownTenants"`      // Discovered
    PendingTenants   []string `json:"pendingTenants"`    // Known but not active
    DegradedTenants  []string `json:"degradedTenants"`   // Failed 3+ times
}
```

**Structured Logs:**
- `connection_mode=lazy` at startup
- `on-demand consumer start for tenant: {id}` when spawning
- `connecting to vhost: tenant={id}` when connecting
- `tenant {id} marked degraded` after max retries

---

### Testing Strategy

**Unit Tests:**
- Startup completes in <1s (0, 100, 500 tenants)
- Concurrent EnsureConsumerStarted spawns exactly 1 consumer
- Exponential backoff sequence (5s, 10s, 20s, 40s)
- Degraded tenant detection after 3 failures

**Integration Tests:**
- Discovery fallback (Redis → API)
- On-demand connection with testcontainers
- Tenant removal cleanup (<30s)

---

### When to Use Multi-Tenant Lazy Consumer

| Scenario | Recommended | Rationale |
|----------|-------------|-----------|
| **10+ tenants** | ✅ Yes | Startup time becomes significant with many tenants |
| **<10 tenants** | ⚠️ Consider | Overhead may not justify complexity |
| **Most tenants inactive** | ✅ Yes | Resources scale with active count only |
| **All tenants active** | ✅ Yes | Still faster startup, resources scale proportionally |
| **Frequent deployments** | ✅ Yes | Fast startup critical for CI/CD velocity |
| **Latency-sensitive** | ✅ Yes* | *First request per tenant: +500ms (acceptable trade-off) |

---

### Common Pitfalls

**❌ Don't:** Start consumers in discovery loop (defeats lazy purpose)
**✅ Do:** Populate knownTenants only, defer connection to trigger

**❌ Don't:** Use global mutex for all tenants (contention)
**✅ Do:** Per-tenant mutex via sync.Map (fine-grained locking)

**❌ Don't:** Fail HTTP request if consumer spawn fails
**✅ Do:** Log warning, let background sync retry

**❌ Don't:** Forget to cleanup on tenant removal
**✅ Do:** Remove from knownTenants, activeTenants, consumerLocks

**❌ Don't:** Retry indefinitely on connection failure
**✅ Do:** Mark degraded after 3 failures, stop retrying

---

### Single-Tenant vs Multi-Tenant Mode

```go
// Support both single-tenant and multi-tenant deployments
if !config.MultiTenantEnabled {
    // Single-tenant: static RabbitMQ connection (no tenant isolation)
    consumer = initSingleTenantConsumer(...)
} else {
    // Multi-tenant: lazy mode with per-tenant vhosts
    consumer = initMultiTenantConsumer(...)
}
```

**Middleware trigger (multi-tenant only):**
```go
if m.consumerTrigger != nil {  // Nil in single-tenant mode
    m.consumerTrigger.EnsureConsumerStarted(ctx, tenantID)
}
```

**Note:** Single-tenant uses a different consumer implementation without tenant isolation. Multi-tenant consumers ALWAYS use lazy mode for optimal startup performance.

---

This section can be added to `golang/multi-tenant.md` as **§24: Message Queue Lazy Consumer Pattern**.