# Go Standards - Multi-Tenant

> **Module:** multi-tenant.md | **Sections:** §23 | **Parent:** [index.md](index.md)

This module covers multi-tenant patterns with Pool Manager.

---

## Multi-Tenant Patterns (CONDITIONAL)

**CONDITIONAL:** Only implement if `MULTI_TENANT_ENABLED=true` is required for your service.

### When to Use Multi-Tenant Mode

| Scenario | Mode | Configuration |
|----------|------|---------------|
| Single customer deployment | Single-tenant | `MULTI_TENANT_ENABLED=false` (default) |
| SaaS with shared infrastructure | Multi-tenant | `MULTI_TENANT_ENABLED=true` |
| Multiple isolated databases per customer | Multi-tenant | Requires Pool Manager |

### Environment Variables

| Env Var | Description | Default | Required |
|---------|-------------|---------|----------|
| `MULTI_TENANT_ENABLED` | Enable multi-tenant mode | `false` | Yes |
| `POOL_MANAGER_URL` | Pool Manager service URL | - | If multi-tenant |
| `MULTI_TENANT_CACHE_TTL` | Tenant configuration cache duration | `24h` | No |

**Example `.env` for multi-tenant:**
```bash
MULTI_TENANT_ENABLED=true
POOL_MANAGER_URL=http://pool-manager:4003
MULTI_TENANT_CACHE_TTL=24h
```

### Configuration

```go
// internal/bootstrap/config.go
type Config struct {
    // Multi-Tenant Configuration
    MultiTenantEnabled  bool   `env:"MULTI_TENANT_ENABLED" default:"false"`
    PoolManagerURL      string `env:"POOL_MANAGER_URL"`
    MultiTenantCacheTTL string `env:"MULTI_TENANT_CACHE_TTL" default:"24h"`

    // Prefixed DB vars (unified deployment)
    PrefixedPrimaryDBHost string `env:"DB_TRANSACTION_HOST"`

    // Fallback DB vars (standalone deployment)
    PrimaryDBHost string `env:"DB_HOST"`
}

// Environment fallback pattern
func envFallback(prefixed, fallback string) string {
    if prefixed != "" {
        return prefixed
    }
    return fallback
}
```

### JWT Tenant Extraction

**Claim key:** `tenantId` (camelCase, hardcoded)

```go
// internal/bootstrap/middleware.go
func (m *Middleware) extractTenantIDFromToken(c *fiber.Ctx) (string, error) {
    // Get token from Authorization header
    authHeader := c.Get("Authorization")
    if authHeader == "" {
        return "", errors.New("authorization header required")
    }

    tokenString := strings.TrimPrefix(authHeader, "Bearer ")

    // Parse without validation (validation done by auth middleware)
    token, _, err := jwt.NewParser().ParseUnverified(tokenString, jwt.MapClaims{})
    if err != nil {
        return "", fmt.Errorf("failed to parse token: %w", err)
    }

    claims, ok := token.Claims.(jwt.MapClaims)
    if !ok {
        return "", errors.New("invalid token claims")
    }

    // Extract tenantId (hardcoded claim key)
    tenantID, ok := claims["tenantId"].(string)
    if !ok || tenantID == "" {
        return "", errors.New("tenantId claim not found in token")
    }

    return tenantID, nil
}
```

### Context Injection Middleware

```go
// internal/bootstrap/middleware.go
func (m *Middleware) WithTenantDB(c *fiber.Ctx) error {
    ctx := c.UserContext()
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "middleware.with_tenant_db")
    defer span.End()

    // Skip for public endpoints
    if m.isPublicPath(c.Path()) {
        return c.Next()
    }

    // Skip if not multi-tenant mode
    if !m.pool.IsMultiTenant() {
        return c.Next()
    }

    // Extract tenant ID from JWT
    tenantID, err := m.extractTenantIDFromToken(c)
    if err != nil {
        logger.Errorf("Failed to extract tenant ID: %v", err)
        return libHTTP.Unauthorized(c, "TENANT_ID_REQUIRED", "Unauthorized",
            "tenantId claim is required in JWT token")
    }

    // Inject tenant ID into context
    ctx = poolmanager.ContextWithTenantID(ctx, tenantID)

    // Get tenant-specific database connection
    conn, err := m.pool.GetConnection(ctx, tenantID)
    if err != nil {
        if errors.Is(err, poolmanager.ErrTenantNotFound) {
            return libHTTP.NotFound(c, "TENANT_NOT_FOUND", "Not Found", "tenant not found")
        }
        return libHTTP.InternalServerError(c, "CONNECTION_ERROR", "Internal Server Error",
            "failed to establish database connection")
    }

    db, err := conn.GetDB()
    if err != nil {
        return libHTTP.InternalServerError(c, "DB_ERROR", "Internal Server Error",
            "failed to get database interface")
    }

    // Inject connection into context
    ctx = poolmanager.ContextWithPGConnection(ctx, db)
    c.SetUserContext(ctx)

    return c.Next()
}

func (m *Middleware) isPublicPath(path string) bool {
    publicPaths := []string{"/health", "/version", "/swagger"}
    for _, p := range publicPaths {
        if strings.HasPrefix(path, p) {
            return true
        }
    }
    return false
}
```

### Database Connection in Repositories

```go
// internal/adapters/postgres/repository.go
func (r *Repository) Create(ctx context.Context, entity *Entity) (*Entity, error) {
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "repository.entity.create")
    defer span.End()

    // Get tenant-specific connection from context
    db, err := poolmanager.GetPostgresForTenant(ctx)
    if err != nil {
        libOpentelemetry.HandleSpanError(&span, "Failed to get database connection", err)
        logger.Errorf("Failed to get database connection: %v", err)
        return nil, err
    }

    // Use db for queries - automatically scoped to tenant
    query := `INSERT INTO entities (...) VALUES (...) RETURNING *`
    row := db.QueryRowContext(ctx, query, ...)

    // ... rest of implementation
}
```

### Redis Key Prefixing

```go
// internal/adapters/redis/repository.go
func (r *RedisRepository) Set(ctx context.Context, key, value string, ttl time.Duration) error {
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "redis.set")
    defer span.End()

    // Tenant-aware key prefixing (adds {tenantId}: prefix if multi-tenant)
    key = poolmanager.GetKeyFromContext(ctx, key)

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
    rabbitMQPool    *poolmanager.RabbitMQPool
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
func NewProducerMultiTenant(pool *poolmanager.RabbitMQPool) *ProducerRepository {
    return &ProducerRepository{
        rabbitMQPool:    pool,
        multiTenantMode: true,
    }
}

func (p *ProducerRepository) Publish(ctx context.Context, exchange, key string, message []byte) error {
    // Inject tenant ID header
    tenantID := poolmanager.GetTenantID(ctx)
    headers := amqp.Table{}
    if tenantID != "" {
        headers["X-Tenant-ID"] = tenantID
    }

    if p.multiTenantMode {
        // Get tenant-specific channel
        channel, err := p.rabbitMQPool.GetChannel(ctx, tenantID)
        if err != nil {
            return err
        }
        return channel.PublishWithContext(ctx, exchange, key, false, false,
            amqp.Publishing{Body: message, Headers: headers})
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
    tenantDB, err := poolmanager.GetMongoForTenant(ctx)
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

func (r *MetadataMongoDBRepository) FindByEntity(ctx context.Context, collection, id string) (*Metadata, error) {
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "mongodb.find_by_entity")
    defer span.End()

    tenantDB, err := poolmanager.GetMongoForTenant(ctx)
    if err != nil {
        libOpentelemetry.HandleSpanError(&span, "Failed to get database", err)
        return nil, err
    }

    coll := tenantDB.Collection(strings.ToLower(collection))

    var record MetadataMongoDBModel
    if err = coll.FindOne(ctx, bson.M{"entity_id": id}).Decode(&record); err != nil {
        if errors.Is(err, mongo.ErrNoDocuments) {
            return nil, nil
        }
        return nil, err
    }

    return record.ToEntity(), nil
}
```

### MongoDB Pool Initialization

```go
// internal/bootstrap/config.go
func initMultiTenantPools(cfg *Config, logger libLog.Logger) *MultiTenantPools {
    poolManagerClient := poolmanager.NewClient(cfg.PoolManagerURL, logger)

    // Create MongoDB pool with module-specific credentials
    mongoPool := poolmanager.NewMongoPool(poolManagerClient, serviceName,
        poolmanager.WithMongoModule("transaction"),
        poolmanager.WithMongoLogger(logger),
    )
    logger.Info("Created MongoDB connection pool for multi-tenant mode")

    return &MultiTenantPools{
        MongoPool: mongoPool,
        // ... other pools
    }
}
```

### MongoDB Context Injection in Middleware

```go
// internal/bootstrap/middleware.go
func (m *Middleware) WithTenantDB(c *fiber.Ctx) error {
    // ... tenant extraction code ...

    // Inject MongoDB if pool configured
    if m.mongoPool != nil {
        mongoDB, err := m.mongoPool.GetDatabaseForTenant(ctx, tenantID)
        if err != nil {
            logger.Errorf("Failed to get MongoDB connection for tenant %s: %v", tenantID, err)
            return libHTTP.InternalServerError(c, "TENANT_MONGO_ERROR", "Internal Server Error",
                "failed to resolve tenant MongoDB connection")
        }

        ctx = poolmanager.ContextWithTenantMongo(ctx, mongoDB)
        logger.Infof("Set MongoDB connection for tenant: %s (db: %s)", tenantID, mongoDB.Name())
    }

    c.SetUserContext(ctx)
    return c.Next()
}
```

### MongoDB in RabbitMQ Consumer (Async Context)

```go
// internal/bootstrap/rabbitmq_consumer.go
func (c *MultiTenantConsumer) injectTenantDBConnections(ctx context.Context, tenantID string, logger libLog.Logger) (context.Context, error) {
    // Inject MongoDB connection (optional - service may not use MongoDB)
    if c.mongoPool != nil {
        mongoDB, err := c.mongoPool.GetDatabaseForTenant(ctx, tenantID)
        if err != nil {
            // MongoDB is optional for some services - warn but don't fail
            logger.Warnf("Failed to get MongoDB for tenant %s: %v (continuing without MongoDB)", tenantID, err)
        } else {
            ctx = poolmanager.ContextWithTenantMongo(ctx, mongoDB)
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
    var producer rabbitmq.ProducerRepository

    if cfg.MultiTenantEnabled {
        // Multi-tenant mode: use pool manager
        poolClient := poolmanager.NewClient(cfg.PoolManagerURL, logger)
        rabbitPool := poolmanager.NewRabbitMQPool(poolClient, serviceName, logger)
        producer = rabbitmq.NewProducerMultiTenant(rabbitPool)
    } else {
        // Single-tenant mode: use static connection
        conn, err := libRabbitmq.NewRabbitMQConnection(cfg.RabbitMQURL)
        if err != nil {
            return nil, err
        }
        producer = rabbitmq.NewProducer(conn)
    }

    return &Service{producer: producer}, nil
}
```

### Testing Multi-Tenant Code

#### Unit Tests with Mock Tenant Context

```go
// internal/service/user_service_test.go
func TestUserService_Create_WithTenantContext(t *testing.T) {
    // Setup tenant context
    tenantID := "tenant-123"
    ctx := poolmanager.ContextWithTenantID(context.Background(), tenantID)

    // Mock database connection
    mockDB := setupMockDB(t)
    ctx = poolmanager.ContextWithPGConnection(ctx, mockDB)

    // Create service with mock dependencies
    repo := repository.NewUserRepository()
    service := service.NewUserService(repo, logger)

    // Execute
    input := &CreateUserInput{Name: "John", Email: "john@example.com"}
    result, err := service.Create(ctx, input)

    // Assert
    require.NoError(t, err)
    assert.Equal(t, "John", result.Name)
    assert.Equal(t, tenantID, result.TenantID)
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
            wantErr:  false, // Different tenant = allowed
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Inject tenant-specific context
            ctx := poolmanager.ContextWithTenantID(context.Background(), tt.tenantID)
            ctx = poolmanager.ContextWithPGConnection(ctx, mockDB)

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

#### Integration Tests with testcontainers

```go
// internal/bootstrap/multi_tenant_integration_test.go
func TestMultiTenant_EndToEnd(t *testing.T) {
    ctx := context.Background()

    // Setup PostgreSQL container
    pgContainer, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
        ContainerRequest: testcontainers.ContainerRequest{
            Image:        "postgres:16-alpine",
            ExposedPorts: []string{"5432/tcp"},
            Env: map[string]string{
                "POSTGRES_USER":     "test",
                "POSTGRES_PASSWORD": "test",
                "POSTGRES_DB":       "tenant_test",
            },
            WaitingFor: wait.ForLog("database system is ready to accept connections"),
        },
        Started: true,
    })
    require.NoError(t, err)
    defer pgContainer.Terminate(ctx)

    // Get container host/port
    host, _ := pgContainer.Host(ctx)
    port, _ := pgContainer.MappedPort(ctx, "5432")

    // Set environment variables with t.Setenv
    t.Setenv("DB_HOST", host)
    t.Setenv("DB_PORT", port.Port())
    t.Setenv("DB_USER", "test")
    t.Setenv("DB_PASSWORD", "test")
    t.Setenv("DB_NAME", "tenant_test")
    t.Setenv("MULTI_TENANT_ENABLED", "true")
    t.Setenv("POOL_MANAGER_URL", "http://mock-pool-manager:4003")

    // Initialize service
    cfg := &Config{}
    require.NoError(t, libCommons.SetConfigFromEnvVars(cfg))

    // Create Pool Manager mock
    poolMock := setupMockPoolManager(t, cfg.PoolManagerURL)
    defer poolMock.Close()

    // Test tenant-specific database access
    tenantID := "tenant-123"
    ctx = poolmanager.ContextWithTenantID(ctx, tenantID)

    // ... test multi-tenant operations
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
            name: "tenant not found in Pool Manager",
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
            // Setup Fiber context
            app := fiber.New()
            ctx := app.AcquireCtx(&fasthttp.RequestCtx{})
            defer app.ReleaseCtx(ctx)

            tt.setupContext(ctx)

            // Execute middleware
            err := middleware.WithTenantDB(ctx)

            // Assert
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
        extractedTenant := poolmanager.GetTenantID(ctx)
        assert.Equal(t, tenantID, extractedTenant)
    })
}
```

#### Testing Redis Key Prefixing

```go
func TestRedisRepository_MultiTenant_KeyPrefixing(t *testing.T) {
    t.Run("prefixes keys with tenant ID", func(t *testing.T) {
        tenantID := "tenant-789"
        ctx := poolmanager.ContextWithTenantID(context.Background(), tenantID)

        repo := NewRedisRepository(redisConn)

        // Set value
        err := repo.Set(ctx, "user:session", "value123", 3600)
        require.NoError(t, err)

        // Verify key was prefixed
        // Expected key: {tenant-789}:user:session
        key := poolmanager.GetKeyFromContext(ctx, "user:session")
        assert.Equal(t, "{tenant-789}:user:session", key)
    })

    t.Run("single-tenant mode does not prefix keys", func(t *testing.T) {
        // Context without tenant ID
        ctx := context.Background()

        repo := NewRedisRepository(redisConn)

        // Key should NOT be prefixed
        key := poolmanager.GetKeyFromContext(ctx, "user:session")
        assert.Equal(t, "user:session", key)
    })
}
```

### Error Handling

| Error | HTTP Status | Code | When |
|-------|-------------|------|------|
| Missing tenantId claim | 401 | `TENANT_ID_REQUIRED` | JWT doesn't have tenantId |
| Tenant not found | 404 | `TENANT_NOT_FOUND` | Tenant not registered in Pool Manager |
| Tenant not provisioned | 422 | `TENANT_NOT_PROVISIONED` | Database schema not initialized |
| Connection error | 500 | `CONNECTION_ERROR` | Failed to get tenant connection |

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "We only have one customer" | Requirements change. Multi-tenant is easy to add now, hard later. | **Design for multi-tenant, deploy as single** |
| "Pool Manager adds complexity" | Complexity is in connection management anyway. Pool Manager standardizes it. | **Use Pool Manager for multi-tenant** |
| "JWT parsing is expensive" | Parse once in middleware, use from context everywhere. | **Extract tenant once, propagate via context** |
| "We'll add tenant isolation later" | Retrofitting tenant isolation is a rewrite. | **Build tenant-aware from the start** |

### Checklist

**Environment Variables:**
- [ ] `MULTI_TENANT_ENABLED` in config struct (default: `false`)
- [ ] `POOL_MANAGER_URL` in config struct (required if multi-tenant)
- [ ] `MULTI_TENANT_CACHE_TTL` in config struct (default: `24h`)

**Middleware & Context:**
- [ ] JWT tenant extraction middleware (claim key: `tenantId`)
- [ ] `poolmanager.ContextWithTenantID()` in middleware
- [ ] Public endpoints (`/health`, `/version`, `/swagger`) bypass tenant middleware

**Repositories:**
- [ ] `poolmanager.GetPostgresForTenant(ctx)` in PostgreSQL repositories
- [ ] `poolmanager.GetKeyFromContext(ctx, key)` for Redis keys
- [ ] `poolmanager.GetMongoForTenant(ctx)` in MongoDB repositories (if using MongoDB)
- [ ] `poolmanager.ContextWithTenantMongo()` in middleware (if using MongoDB)

**Async Processing:**
- [ ] Tenant ID header (`X-Tenant-ID`) in RabbitMQ messages
- [ ] MongoDB injection in RabbitMQ consumers for async processing
- [ ] PostgreSQL injection in RabbitMQ consumers for async processing
- [ ] Proper error codes for tenant-related failures

**Testing:**
- [ ] Unit tests with mock tenant context (`poolmanager.ContextWithTenantID`)
- [ ] Tenant isolation tests (verify data separation between tenants)
- [ ] Error case tests (missing tenant, invalid tenant, tenant not found)
- [ ] Integration tests with testcontainers
- [ ] RabbitMQ consumer tests (X-Tenant-ID header extraction)
- [ ] Redis key prefixing tests (verify tenant prefix applied)

---

