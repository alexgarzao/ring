# Go Standards - Multi-Tenant

> **Module:** multi-tenant.md | **Sections:** §24 | **Parent:** [index.md](index.md)

This module covers multi-tenant patterns with Tenant Manager.

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [Multi-Tenant Patterns (CONDITIONAL)](#multi-tenant-patterns-conditional) | Configuration, JWT extraction, context injection |
| 2 | [Tenant Isolation Verification (⚠️ CONDITIONAL)](#tenant-isolation-verification-conditional) | IDOR prevention, tenant verification in queries |
| 24 | [Multi-Tenant Message Queue Consumers (Lazy Mode)](#multi-tenant-message-queue-consumers-lazy-mode) | Lazy consumer initialization, on-demand connection, exponential backoff |

---

## Multi-Tenant Patterns (CONDITIONAL)

**CONDITIONAL:** Only implement if `MULTI_TENANT_ENABLED=true` is required for your service.

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

**Example `.env` for multi-tenant:**
```bash
MULTI_TENANT_ENABLED=true
MULTI_TENANT_URL=http://tenant-manager:4003
```

### Configuration

```go
// internal/bootstrap/config.go
type Config struct {
    // Multi-Tenant Configuration
    MultiTenantEnabled bool   `env:"MULTI_TENANT_ENABLED" default:"false"`
    MultiTenantURL     string `env:"MULTI_TENANT_URL"`

    // PostgreSQL Primary
    PrimaryDBHost     string `env:"DB_HOST"`
    PrimaryDBUser     string `env:"DB_USER"`
    PrimaryDBPassword string `env:"DB_PASSWORD"`
    PrimaryDBName     string `env:"DB_NAME"`
    PrimaryDBPort     string `env:"DB_PORT"`
    PrimaryDBSSLMode  string `env:"DB_SSLMODE"`

    // PostgreSQL connection pool
    MaxOpenConnections int `env:"DB_MAX_OPEN_CONNS"`
    MaxIdleConnections int `env:"DB_MAX_IDLE_CONNS"`
}
```

### Module Constants

Multi-tenant services use module constants to route connections to the correct database:

```go
// pkg/constant/module.go
const (
    // ModuleOnboarding routes PostgreSQL connections for the onboarding component.
    ModuleOnboarding = "onboarding"

    // ModuleTransaction routes PostgreSQL connections for the transaction component.
    ModuleTransaction = "transaction"
)
```

### JWT Tenant Extraction

**Claim key:** `tenantId` (camelCase, hardcoded)

```go
// internal/bootstrap/middleware.go
func (m *DualPoolMiddleware) extractTenantIDFromToken(c *fiber.Ctx) (string, error) {
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

### DualPoolMiddleware

The middleware routes requests to the correct tenant connection pool based on URL path. It maintains separate pools for onboarding and transaction modules.

```go
// internal/bootstrap/unified-server.go
type DualPoolMiddleware struct {
    onboardingPool       *tenantmanager.TenantConnectionManager
    transactionPool      *tenantmanager.TenantConnectionManager
    onboardingMongoPool  *tenantmanager.MongoManager
    transactionMongoPool *tenantmanager.MongoManager
    logger               libLog.Logger
}

func NewDualPoolMiddleware(pools *MultiTenantPools, logger libLog.Logger) *DualPoolMiddleware {
    return &DualPoolMiddleware{
        onboardingPool:       pools.OnboardingPool,
        transactionPool:      pools.TransactionPool,
        onboardingMongoPool:  pools.OnboardingMongoPool,
        transactionMongoPool: pools.TransactionMongoPool,
        logger:               logger,
    }
}
```

### Path-Based Pool Selection

```go
// internal/bootstrap/unified-server.go

// selectPool determines which PostgreSQL pool to use based on the request path.
func (m *DualPoolMiddleware) selectPool(path string) *tenantmanager.TenantConnectionManager {
    if m.isTransactionPath(path) {
        return m.transactionPool
    }
    return m.onboardingPool
}

// isTransactionPath checks if the path belongs to the transaction module.
func (m *DualPoolMiddleware) isTransactionPath(path string) bool {
    transactionPaths := []string{
        "/transactions",
        "/operations",
        "/balances",
        "/asset-rates",
        "/operation-routes",
        "/transaction-routes",
    }

    for _, tp := range transactionPaths {
        if strings.Contains(path, tp) {
            return true
        }
    }

    return false
}

// isPublicPath checks if the path is a public endpoint that doesn't require tenant context.
func (m *DualPoolMiddleware) isPublicPath(path string) bool {
    publicPaths := []string{"/health", "/version", "/swagger"}
    for _, pp := range publicPaths {
        if path == pp || strings.HasPrefix(path, pp) {
            return true
        }
    }
    return false
}
```

### Context Injection Middleware

```go
// internal/bootstrap/unified-server.go
func (m *DualPoolMiddleware) WithTenantDB(c *fiber.Ctx) error {
    path := c.Path()

    // Skip public endpoints
    if m.isPublicPath(path) {
        return c.Next()
    }

    // Select the appropriate pool based on request path
    pool := m.selectPool(path)

    if pool == nil {
        return c.Next()
    }

    // Single-tenant mode: pass through
    if !pool.IsMultiTenant() {
        return c.Next()
    }

    ctx := libOpentelemetry.ExtractHTTPContext(c)
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "middleware.dual_pool.with_tenant_db")
    defer span.End()

    // Extract tenant ID from JWT token
    tenantID, err := m.extractTenantIDFromToken(c)
    if err != nil {
        logger.Errorf("Failed to extract tenant ID: %v", err)
        libOpentelemetry.HandleSpanBusinessErrorEvent(&span, "Failed to extract tenant ID", err)
        return libHTTP.Unauthorized(c, "TENANT_ID_REQUIRED", "Unauthorized",
            "tenantId claim is required in JWT token for multi-tenant mode")
    }

    // Store tenant ID in context
    ctx = tenantmanager.ContextWithTenantID(ctx, tenantID)

    // Get tenant-specific connection from the selected pool
    conn, err := pool.GetConnection(ctx, tenantID)
    if err != nil {
        logger.Errorf("Failed to get PostgreSQL connection for tenant %s: %v", tenantID, err)
        libOpentelemetry.HandleSpanError(&span, "Failed to get tenant connection", err)

        if errors.Is(err, tenantmanager.ErrTenantNotFound) {
            return libHTTP.NotFound(c, "TENANT_NOT_FOUND", "Not Found", "tenant not found")
        }

        if errors.Is(err, tenantmanager.ErrManagerClosed) {
            return libHTTP.JSONResponse(c, http.StatusServiceUnavailable, libCommons.Response{
                Code:    "SERVICE_UNAVAILABLE",
                Title:   "Service Unavailable",
                Message: "Service temporarily unavailable",
            })
        }

        return libHTTP.InternalServerError(c, "CONNECTION_ERROR", "Internal Server Error",
            "failed to establish database connection")
    }

    db, err := conn.GetDB()
    if err != nil {
        return libHTTP.InternalServerError(c, "DB_ERROR", "Internal Server Error",
            "failed to get database interface")
    }

    // CRITICAL: Set BOTH module connections for cross-module in-process calls
    if m.isTransactionPath(path) {
        ctx = tenantmanager.ContextWithModulePGConnection(ctx, constant.ModuleTransaction, db)

        // Also inject onboarding connection for cross-module calls
        if m.onboardingPool != nil && m.onboardingPool.IsMultiTenant() {
            onboardingConn, onboardingErr := m.onboardingPool.GetConnection(ctx, tenantID)
            if onboardingErr == nil {
                onboardingDB, dbErr := onboardingConn.GetDB()
                if dbErr == nil && onboardingDB != nil {
                    ctx = tenantmanager.ContextWithModulePGConnection(ctx, constant.ModuleOnboarding, onboardingDB)
                }
            }
        }
    } else {
        ctx = tenantmanager.ContextWithModulePGConnection(ctx, constant.ModuleOnboarding, db)

        // Also inject transaction connection for cross-module calls
        if m.transactionPool != nil && m.transactionPool.IsMultiTenant() {
            transactionConn, transactionErr := m.transactionPool.GetConnection(ctx, tenantID)
            if transactionErr == nil {
                transactionDB, dbErr := transactionConn.GetDB()
                if dbErr == nil && transactionDB != nil {
                    ctx = tenantmanager.ContextWithModulePGConnection(ctx, constant.ModuleTransaction, transactionDB)
                }
            }
        }
    }

    // Handle MongoDB if pool is configured
    mongoPool := m.selectMongoPool(path)
    if mongoPool != nil {
        mongoDB, mongoErr := mongoPool.GetDatabaseForTenant(ctx, tenantID)
        if mongoErr != nil {
            logger.Errorf("Failed to get MongoDB connection for tenant %s: %v", tenantID, mongoErr)
            return libHTTP.InternalServerError(c, "TENANT_MONGO_ERROR", "Internal Server Error",
                "failed to resolve tenant MongoDB connection")
        }

        ctx = tenantmanager.ContextWithTenantMongo(ctx, mongoDB)
    }

    c.SetUserContext(ctx)

    return c.Next()
}
```

### Database Connection in Repositories

Repositories use module-specific getters to retrieve tenant connections from context:

```go
// internal/adapters/postgres/organization/organization.postgresql.go (Onboarding module)
func (r *OrganizationPostgreSQLRepository) Create(ctx context.Context, org *mmodel.Organization) (*mmodel.Organization, error) {
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "postgres.create_organization")
    defer span.End()

    // Get onboarding module connection from context
    db, err := tenantmanager.GetModulePostgresForTenant(ctx, constant.ModuleOnboarding)
    if err != nil {
        libOpentelemetry.HandleSpanError(&span, "Failed to get database connection", err)
        logger.Errorf("Failed to get database connection: %v", err)
        return nil, err
    }

    record := &OrganizationPostgreSQLModel{}
    record.FromEntity(org)

    // Use db for queries - automatically scoped to tenant's database
    // ...
}
```

```go
// internal/adapters/postgres/transaction/transaction.postgresql.go (Transaction module)
func (r *TransactionPostgreSQLRepository) Create(ctx context.Context, txn *Transaction) (*Transaction, error) {
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "postgres.create_transaction")
    defer span.End()

    // Get transaction module connection from context
    db, err := tenantmanager.GetModulePostgresForTenant(ctx, constant.ModuleTransaction)
    if err != nil {
        libOpentelemetry.HandleSpanError(&span, "Failed to get database connection", err)
        logger.Errorf("Failed to get database connection: %v", err)
        return nil, err
    }

    record := &TransactionPostgreSQLModel{}
    record.FromEntity(txn)

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

    return rds.Set(ctx, key, value, ttl*time.Second).Err()
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

### Multi-Tenant Pool Initialization

```go
// internal/bootstrap/config.go

// MultiTenantPools holds the connection pools for the unified ledger.
// The Tenant Manager returns separate database credentials for each module.
type MultiTenantPools struct {
    OnboardingPool       *tenantmanager.TenantConnectionManager
    TransactionPool      *tenantmanager.TenantConnectionManager
    OnboardingMongoPool  *tenantmanager.MongoManager
    TransactionMongoPool *tenantmanager.MongoManager
}

func initMultiTenantPools(cfg *Config, logger libLog.Logger) *MultiTenantPools {
    // Create Tenant Manager client (shared between all pools)
    tenantManagerClient := tenantmanager.NewClient(cfg.MultiTenantURL, logger)

    // Create default PostgreSQL connections for fallback (single-tenant mode)
    onboardingDefaultConn := &libPostgres.PostgresConnection{
        ConnectionStringPrimary: buildConnString(cfg),
        Component:               "onboarding",
        Logger:                  logger,
        MaxOpenConnections:      cfg.MaxOpenConnections,
        MaxIdleConnections:      cfg.MaxIdleConnections,
    }

    transactionDefaultConn := &libPostgres.PostgresConnection{
        ConnectionStringPrimary: buildConnString(cfg),
        Component:               "transaction",
        Logger:                  logger,
        MaxOpenConnections:      cfg.MaxOpenConnections,
        MaxIdleConnections:      cfg.MaxIdleConnections,
    }

    // Create onboarding pool - orgs, ledgers, accounts, assets, portfolios, segments
    onboardingPool := tenantmanager.NewTenantConnectionManager(tenantManagerClient, "ledger", "onboarding", logger).
        WithConnectionLimits(cfg.MaxOpenConnections, cfg.MaxIdleConnections).
        WithDefaultConnection(onboardingDefaultConn)

    logger.Info("Created onboarding PostgreSQL connection manager for multi-tenant mode")

    // Create transaction pool - transactions, operations, balances, asset-rates, routes
    transactionPool := tenantmanager.NewTenantConnectionManager(tenantManagerClient, "ledger", "transaction", logger).
        WithConnectionLimits(cfg.MaxOpenConnections, cfg.MaxIdleConnections).
        WithDefaultConnection(transactionDefaultConn)

    logger.Info("Created transaction PostgreSQL connection manager for multi-tenant mode")

    // Create MongoDB pools per module
    onboardingMongoPool := tenantmanager.NewMongoManager(tenantManagerClient, "ledger",
        tenantmanager.WithMongoModule("onboarding"),
        tenantmanager.WithMongoLogger(logger),
    )
    logger.Info("Created onboarding MongoDB connection manager for multi-tenant mode")

    transactionMongoPool := tenantmanager.NewMongoManager(tenantManagerClient, "ledger",
        tenantmanager.WithMongoModule("transaction"),
        tenantmanager.WithMongoLogger(logger),
    )
    logger.Info("Created transaction MongoDB connection manager for multi-tenant mode")

    return &MultiTenantPools{
        OnboardingPool:       onboardingPool,
        TransactionPool:      transactionPool,
        OnboardingMongoPool:  onboardingMongoPool,
        TransactionMongoPool: transactionMongoPool,
    }
}
```

### MongoDB in RabbitMQ Consumer (Async Context)

```go
// internal/bootstrap/rabbitmq_consumer.go
func (c *MultiTenantConsumer) injectTenantDBConnections(ctx context.Context, tenantID string, logger libLog.Logger) (context.Context, error) {
    // Inject PostgreSQL connection
    if c.postgresPool != nil {
        pgConn, err := c.postgresPool.GetConnection(ctx, tenantID)
        if err != nil {
            logger.Errorf("Failed to get PostgreSQL connection for tenant %s: %v", tenantID, err)
            return ctx, fmt.Errorf("failed to get PostgreSQL connection: %w", err)
        }

        db, err := pgConn.GetDB()
        if err != nil {
            return ctx, fmt.Errorf("failed to get DB interface: %w", err)
        }

        ctx = tenantmanager.ContextWithModulePGConnection(ctx, constant.ModuleTransaction, db)
        logger.Infof("Injected PostgreSQL connection for tenant: %s", tenantID)
    }

    // Inject MongoDB connection (optional - service may not use MongoDB)
    if c.mongoPool != nil {
        mongoDB, err := c.mongoPool.GetDatabaseForTenant(ctx, tenantID)
        if err != nil {
            // MongoDB is optional for some services - warn but don't fail
            logger.Warnf("Failed to get MongoDB for tenant %s: %v (continuing without MongoDB)", tenantID, err)
        } else {
            ctx = tenantmanager.ContextWithTenantMongo(ctx, mongoDB)
            logger.Infof("Injected MongoDB connection for tenant: %s", tenantID)
        }
    }

    return ctx, nil
}
```

### Conditional Initialization

```go
// internal/bootstrap/service.go
func InitService(cfg *Config) (*Service, error) {
    var tenantPools *MultiTenantPools

    if cfg.MultiTenantEnabled && cfg.MultiTenantURL != "" {
        tenantPools = initMultiTenantPools(cfg, logger)
        logger.Infof("Multi-tenant mode enabled with Tenant Manager URL: %s", cfg.MultiTenantURL)
    } else {
        logger.Info("Running in SINGLE-TENANT MODE")
    }

    // Create unified server with optional tenant pools
    server := NewUnifiedServer(cfg.ServerAddress, logger, tenantPools)

    // Register multi-tenant middleware if pools exist
    if tenantPools != nil {
        dualPoolMid := NewDualPoolMiddleware(tenantPools, logger)
        server.Use(dualPoolMid.WithTenantDB)
    }

    return &Service{server: server}, nil
}
```

### Error Handler

```go
// internal/bootstrap/unified-server.go
func handleUnifiedServerError(c *fiber.Ctx, err error) error {
    // Check for unprovisioned tenant database (SQLSTATE 42P01)
    if tenantmanager.IsTenantNotProvisionedError(err) {
        return libHTTP.UnprocessableEntity(c, "TENANT_NOT_PROVISIONED", "Unprocessable Entity",
            "The tenant database schema has not been initialized. Please contact support.")
    }

    // Default error handling
    code := fiber.StatusInternalServerError
    var e *fiber.Error
    if errors.As(err, &e) {
        code = e.Code
    }

    return c.Status(code).JSON(libCommons.Response{
        Code:    http.StatusText(code),
        Title:   http.StatusText(code),
        Message: err.Error(),
    })
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

    // Mock database connection with module-specific injection
    mockDB := setupMockDB(t)
    ctx = tenantmanager.ContextWithModulePGConnection(ctx, constant.ModuleOnboarding, mockDB)

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
            // Inject tenant-specific context with module connection
            ctx := tenantmanager.ContextWithTenantID(context.Background(), tt.tenantID)
            ctx = tenantmanager.ContextWithModulePGConnection(ctx, constant.ModuleOnboarding, mockDB)

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
| Connection error | 500 | `CONNECTION_ERROR` | Failed to get tenant connection |
| Manager closed | 503 | `SERVICE_UNAVAILABLE` | Connection manager has been shut down |

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
// internal/adapters/postgres/transaction/transaction.postgresql.go
func (r *TransactionPostgreSQLRepository) Find(ctx context.Context, organizationID, ledgerID, id uuid.UUID) (*Transaction, error) {
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "postgres.find_transaction")
    defer span.End()

    db, err := tenantmanager.GetModulePostgresForTenant(ctx, constant.ModuleTransaction)
    if err != nil {
        return nil, err
    }

    // Query scoped by organization_id and ledger_id
    find := squirrel.Select(transactionColumnList...).
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
query := `SELECT * FROM transactions WHERE id = $1`  // WRONG: No organization_id/ledger_id
row := db.QueryRowContext(ctx, query, id)

// ❌ FORBIDDEN: Missing ledger_id in query
query := `SELECT * FROM transactions WHERE organization_id = $1 AND id = $2`  // WRONG: No ledger_id

// ❌ FORBIDDEN: Post-query entity check
txn, err := r.GetByID(ctx, id)
if txn.OrganizationID != organizationID {  // WRONG: Data already fetched
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

### Anti-Rationalization Table (General)

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "We only have one customer" | Requirements change. Multi-tenant is easy to add now, hard later. | **Design for multi-tenant, deploy as single** |
| "Tenant Manager adds complexity" | Complexity is in connection management anyway. Tenant Manager standardizes it. | **Use Tenant Manager for multi-tenant** |
| "JWT parsing is expensive" | Parse once in middleware, use from context everywhere. | **Extract tenant once, propagate via context** |
| "We'll add tenant isolation later" | Retrofitting tenant isolation is a rewrite. | **Build tenant-aware from the start** |

### Checklist

**Environment Variables:**
- [ ] `MULTI_TENANT_ENABLED` in config struct (default: `false`)
- [ ] `MULTI_TENANT_URL` in config struct (required if multi-tenant)

**Architecture:**
- [ ] `MultiTenantPools` struct with onboarding + transaction pools (PG and Mongo)
- [ ] `DualPoolMiddleware` with path-based pool selection
- [ ] Module constants defined (`constant.ModuleOnboarding`, `constant.ModuleTransaction`)
- [ ] `NewTenantConnectionManager` with `.WithConnectionLimits()` and `.WithDefaultConnection()`
- [ ] Cross-module connection injection (both modules in context for in-process calls)

**Middleware & Context:**
- [ ] JWT tenant extraction middleware (claim key: `tenantId`)
- [ ] `tenantmanager.ContextWithTenantID()` in middleware
- [ ] `tenantmanager.ContextWithModulePGConnection(ctx, module, db)` for PostgreSQL
- [ ] Public endpoints (`/health`, `/version`, `/swagger`) bypass tenant middleware
- [ ] `tenantmanager.ErrManagerClosed` → 503 handling
- [ ] `tenantmanager.IsTenantNotProvisionedError()` in error handler → 422

**Repositories:**
- [ ] `tenantmanager.GetModulePostgresForTenant(ctx, module)` in PostgreSQL repositories
- [ ] `tenantmanager.GetKeyFromContext(ctx, key)` for Redis keys
- [ ] `tenantmanager.GetMongoForTenant(ctx)` in MongoDB repositories (if using MongoDB)
- [ ] `tenantmanager.ContextWithTenantMongo()` in middleware (if using MongoDB)

**Async Processing:**
- [ ] Tenant ID header (`X-Tenant-ID`) in RabbitMQ messages
- [ ] `ContextWithModulePGConnection` in RabbitMQ consumer with correct module
- [ ] MongoDB injection in RabbitMQ consumers for async processing
- [ ] Proper error codes for tenant-related failures

**Testing:**
- [ ] Unit tests with mock tenant context (`tenantmanager.ContextWithModulePGConnection`)
- [ ] Tenant isolation tests (verify data separation between tenants)
- [ ] Error case tests (missing tenant, invalid tenant, tenant not found)
- [ ] Integration tests with two distinct tenants verifying cross-tenant isolation
- [ ] RabbitMQ consumer tests (X-Tenant-ID header extraction)
- [ ] Redis key prefixing tests (verify tenant prefix applied)

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
- Public (no authentication - internal trusted service)
- Returns minimal info (id, name, status only)
- Filters by service (optional query param)

#### 2. Consumer Manager (lib-commons)

**Responsibility:** Manage lifecycle of message consumers across tenants with lazy initialization.

**Key methods:**
```go
type MultiTenantConsumer struct {
    knownTenants map[string]bool        // Discovered tenants
    activeTenants map[string]CancelFunc // Running consumers
    consumerLocks sync.Map               // Per-tenant mutexes
    retryState sync.Map                  // Failure tracking
}

// Discover tenants without connecting (non-blocking, <1s)
func (c *MultiTenantConsumer) Run(ctx context.Context) error

// Ensure consumer is active for tenant (idempotent, thread-safe)
func (c *MultiTenantConsumer) EnsureConsumerStarted(ctx context.Context, tenantID string) error

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
            if err := consumer.EnsureConsumerStarted(ctx, tenantID); err != nil {
                logger.Warnf("failed to ensure consumer: %v", err)
                // Don't fail request - consumer retries via background sync
            }
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
func (c *Consumer) EnsureConsumerStarted(ctx, tenantID string) error {
    // Fast path: check if already active (read lock)
    c.mu.RLock()
    if _, exists := c.activeTenants[tenantID]; exists {
        c.mu.RUnlock()
        return nil  // Already running
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
        return nil  // Another goroutine created it
    }
    c.mu.RUnlock()

    // Spawn consumer
    return c.startTenantConsumer(ctx, tenantID)
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
    consumer.Run(ctx)  // Non-blocking, returns <1s

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

    // Lazy mode trigger
    if m.consumer != nil {
        m.consumer.EnsureConsumerStarted(c.UserContext(), tenantID)
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