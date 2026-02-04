# Go Standards - Idempotency

> **Module:** idempotency.md | **Sections:** §22 | **Parent:** [index.md](index.md)

This module covers idempotency patterns for transaction APIs.

---

## Idempotency Patterns (MANDATORY for Transaction APIs)

**MUST implement idempotency:** All APIs that create resources or trigger side effects. This prevents duplicate operations from network retries, client bugs, or user double-clicks. **HARD GATE**

### Why This Pattern Is Mandatory

| Problem | Consequence | Solution |
|---------|-------------|----------|
| Network retry creates duplicate | Double charge, duplicate records | Idempotency key deduplication |
| Client retries after timeout | Operation executed twice | Cached response replay |
| User double-clicks submit | Two identical transactions | Request fingerprinting |
| Load balancer retry | Multiple side effects | Atomic lock with SetNX |

### HTTP Headers (lib-commons constants)

| Constant | Header | Type | Description |
|----------|--------|------|-------------|
| `libConstants.IdempotencyKey` | `X-Idempotency` | string | Client-provided unique key |
| `libConstants.IdempotencyTTL` | `X-TTL` | int | Cache TTL in seconds |
| `libConstants.IdempotencyReplayed` | `X-Idempotency-Replayed` | bool | Response header: `"true"` if cached |

### Implementation Decisions (Ask Before Implementing)

**HARD GATE:** Before implementing idempotency, ask the user about the key scope.

**ring:AskUserQuestion:** "What should be the idempotency key scope for this service? Please specify the identifiers to use (e.g., `organizationID:ledgerID`, `organizationID`, `tenantID`, or empty for global)."

The user defines the scope based on their domain model. Examples:

| User Response | Scope Build Code | Key Format |
|---------------|------------------|------------|
| `organizationID:ledgerID` | `scope := orgID.String() + ":" + ledgerID.String()` | `idempotency:{orgId:ledgerId:key}` |
| `organizationID` | `scope := orgID.String()` | `idempotency:{orgId:key}` |
| `tenantID` | `scope := tenantID` | `idempotency:{tenantId:key}` |
| `accountID:transactionType` | `scope := accountID.String() + ":" + txType` | `idempotency:{accountId:txType:key}` |
| (empty/global) | `scope := ""` | `idempotency:{key}` |

**Note:** The scope is domain-specific. Use whatever identifiers make sense for your service's isolation requirements.

---

### Implementation Pattern (midaz reference)

#### 1. Header Extraction

```go
// pkg/net/http/httputils.go
import (
    libConstants "github.com/LerianStudio/lib-commons/v2/commons/constants"
    libRedis "github.com/LerianStudio/lib-commons/v2/commons/redis"
)

// GetIdempotencyKeyAndTTL returns idempotency key and ttl if pass through.
func GetIdempotencyKeyAndTTL(c *fiber.Ctx) (string, time.Duration) {
    ikey := c.Get(libConstants.IdempotencyKey)
    iTTL := c.Get(libConstants.IdempotencyTTL)

    // Interpret TTL as seconds count. Downstream Redis helpers multiply by time.Second.
    t, err := strconv.Atoi(iTTL)
    if err != nil || t <= 0 {
        t = libRedis.TTL
    }

    ttl := time.Duration(t)

    return ikey, ttl
}
```

#### 2. Handler Implementation

```go
// internal/adapters/http/in/transaction.go
func (handler *TransactionHandler) createTransaction(c *fiber.Ctx, ...) error {
    ctx := c.UserContext()
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    _, span := tracer.Start(ctx, "handler.create_transaction")
    defer span.End()

    organizationID := c.Locals("organization_id").(uuid.UUID)
    ledgerID := c.Locals("ledger_id").(uuid.UUID)

    // Initialize replay flag
    c.Set(libConstants.IdempotencyReplayed, "false")

    // ... validation code ...

    // Create idempotency span
    ctxIdempotency, spanIdempotency := tracer.Start(ctx, "handler.create_transaction_idempotency")

    // Generate hash from request payload
    ts, _ := libCommons.StructToJSONString(parserDSL)
    hash := libCommons.HashSHA256(ts)
    key, ttl := http.GetIdempotencyKeyAndTTL(c)

    // Check or create idempotency lock
    value, err := handler.Command.CreateOrCheckIdempotencyKey(
        ctxIdempotency, organizationID, ledgerID, key, hash, ttl)
    if err != nil {
        libOpentelemetry.HandleSpanBusinessErrorEvent(&spanIdempotency,
            "Error on create or check redis idempotency key", err)
        spanIdempotency.End()

        logger.Infof("Error on create or check redis idempotency key: %v", err.Error())

        return http.WithError(c, err)
    } else if !libCommons.IsNilOrEmpty(value) {
        // Return cached response
        t := transaction.Transaction{}
        if err = json.Unmarshal([]byte(*value), &t); err != nil {
            libOpentelemetry.HandleSpanError(&spanIdempotency,
                "Error to deserialization idempotency transaction json on redis", err)

            logger.Errorf("Error to deserialization idempotency transaction json on redis: %v", err)
            spanIdempotency.End()

            return http.WithError(c, err)
        }

        spanIdempotency.End()
        c.Set(libConstants.IdempotencyReplayed, "true")

        return http.Created(c, t)
    }

    spanIdempotency.End()

    // ... process transaction ...

    // Cache result asynchronously (non-blocking)
    go handler.Command.SetValueOnExistingIdempotencyKey(
        ctx, organizationID, ledgerID, key, hash, *tran, ttl)

    // Store reverse mapping synchronously (short TTL for lookups)
    handler.Command.SetTransactionIdempotencyMapping(
        ctx, organizationID, ledgerID, tran.ID, key, 5)

    return http.Created(c, tran)
}
```

#### 3. Command Layer (Use Case)

```go
// internal/services/command/create-idempotency-key.go
package command

import (
    "context"
    "errors"
    "time"

    libCommons "github.com/LerianStudio/lib-commons/v2/commons"
    libOpentelemetry "github.com/LerianStudio/lib-commons/v2/commons/opentelemetry"
    "github.com/redis/go-redis/v9"
)

// Caller builds scope based on user's answer to ring:AskUserQuestion.
// The scope is domain-specific - use whatever identifiers the user specified.
//
// Example scope builds:
//   scope := organizationID.String() + ":" + ledgerID.String()  // org:ledger
//   scope := organizationID.String()                            // org only
//   scope := tenantID                                           // tenant
//   scope := accountID.String() + ":" + txType                  // custom domain
//   scope := ""                                                 // global (no scope)

func (uc *UseCase) CreateOrCheckIdempotencyKey(
    ctx context.Context,
    scope string, // Built from domain identifiers per service design
    key, hash string,
    ttl time.Duration,
) (*string, error) {
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "command.create_idempotency_key")
    defer span.End()

    logger.Infof("Trying to create or check idempotency key in redis")

    // Use hash as fallback if no key provided
    if key == "" {
        key = hash
    }

    // Create scoped internal key (multi-tenant isolation)
    internalKey := utils.IdempotencyInternalKey(scope, key)

    // Atomic lock acquisition with SetNX
    success, err := uc.RedisRepo.SetNX(ctx, internalKey, "", ttl)
    if err != nil {
        libOpentelemetry.HandleSpanError(&span,
            "Error to lock idempotency key on redis failed", err)

        logger.Error("Error to lock idempotency key on redis failed:", err.Error())

        return nil, err
    }

    // Lock acquired - first request
    if success {
        return nil, nil
    }

    // Lock exists - check for cached value
    value, err := uc.RedisRepo.Get(ctx, internalKey)
    if err != nil && !errors.Is(err, redis.Nil) {
        libOpentelemetry.HandleSpanError(&span,
            "Error to get idempotency key on redis failed", err)

        logger.Error("Error to get idempotency key on redis failed:", err.Error())

        return nil, err
    }

    // Return cached value if found
    if !libCommons.IsNilOrEmpty(&value) {
        logger.Infof("Found value on redis with this key: %v", internalKey)

        return &value, nil
    }

    // Lock exists but no value - duplicate in-flight request
    err = pkg.ValidateBusinessError(constant.ErrIdempotencyKey,
        "CreateOrCheckIdempotencyKey", key)

    logger.Warnf("Failed, exists value on redis with this key: %v", err)

    return nil, err
}

// SetValueOnExistingIdempotencyKey func that set value on idempotency key to return to user.
func (uc *UseCase) SetValueOnExistingIdempotencyKey(
    ctx context.Context,
    scope string, // Built from domain identifiers per service design
    key, hash string,
    t transaction.Transaction,
    ttl time.Duration,
) {
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "command.set_value_idempotency_key")
    defer span.End()

    logger.Infof("Trying to set value on idempotency key in redis")

    if key == "" {
        key = hash
    }

    internalKey := utils.IdempotencyInternalKey(scope, key)

    value, err := libCommons.StructToJSONString(t)
    if err != nil {
        logger.Error("Err to serialize transaction struct %v\n", err)
    }

    err = uc.RedisRepo.Set(ctx, internalKey, value, ttl)
    if err != nil {
        logger.Error("Error to set value on lock idempotency key on redis:", err.Error())
    }
}

// SetTransactionIdempotencyMapping stores the reverse mapping from transactionID to idempotency key.
// This allows looking up which idempotency key corresponds to a given transaction.
func (uc *UseCase) SetTransactionIdempotencyMapping(
    ctx context.Context,
    scope string, // Built from domain identifiers per service design
    transactionID, idempotencyKey string,
    ttl time.Duration,
) {
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "command.set_transaction_idempotency_mapping")
    defer span.End()

    logger.Infof("Trying to set transaction idempotency mapping in redis for transactionID: %s",
        transactionID)

    reverseKey := utils.IdempotencyReverseKey(scope, transactionID)

    err := uc.RedisRepo.Set(ctx, reverseKey, idempotencyKey, ttl)
    if err != nil {
        libOpentelemetry.HandleSpanError(&span,
            "Error setting transaction idempotency mapping in redis", err)

        logger.Errorf("Error setting transaction idempotency mapping in redis for transactionID %s: %s",
            transactionID, err.Error())
    }
}
```

#### 4. Redis Key Format

**Two isolation levels depending on deployment mode:**

| Mode | Key Format | Isolation |
|------|------------|-----------|
| Single-tenant | `idempotency:{scope:key}` | Query-level filtering |
| Multi-tenant | `{tenantId}:idempotency:{scope:key}` | Connection + Query |

**Scope identifiers** depend on your domain model:

| Domain | Scope Example | Key Format |
|--------|---------------|------------|
| Ledger (midaz) | `organizationID:ledgerID` | `idempotency:{orgId:ledgerId:key}` |
| CRM | `organizationID` | `idempotency:{orgId:key}` |
| Auth | `tenantId` | `idempotency:{tenantId:key}` |
| Simple API | (none) | `idempotency:{key}` |

##### Single-Tenant Mode (default)

```go
// pkg/utils/cache.go

// IdempotencyInternalKey returns a key with scope identifiers for your domain.
// Format: "idempotency:{scope:key}" where scope depends on your domain model.
//
// Examples:
//   - Ledger:  "idempotency:{organizationID:ledgerID:key}"
//   - CRM:     "idempotency:{organizationID:key}"
//   - Simple:  "idempotency:{key}"
func IdempotencyInternalKey(scope, key string) string {
    var builder strings.Builder

    builder.WriteString("idempotency")
    builder.WriteString(keySeparator)       // ":"
    builder.WriteString(beginningKey)        // "{"
    if scope != "" {
        builder.WriteString(scope)
        builder.WriteString(keySeparator)
    }
    builder.WriteString(key)
    builder.WriteString(endKey)              // "}"

    return builder.String()
}

// Domain-specific helper (midaz example with organizationID + ledgerID)
func IdempotencyKeyForLedger(organizationID, ledgerID uuid.UUID, key string) string {
    scope := organizationID.String() + ":" + ledgerID.String()
    return IdempotencyInternalKey(scope, key)
}

// Domain-specific helper (CRM example with organizationID only)
func IdempotencyKeyForOrg(organizationID uuid.UUID, key string) string {
    return IdempotencyInternalKey(organizationID.String(), key)
}
```

##### Multi-Tenant Mode (MULTI_TENANT_ENABLED=true)

When multi-tenant mode is enabled, `poolmanager` adds the tenant prefix automatically:

```go
// In Redis repository layer - applies tenant prefix from context
func (rr *RedisRepository) SetNX(ctx context.Context, key, value string, ttl time.Duration) (bool, error) {
    // poolmanager adds tenantId prefix when MULTI_TENANT_ENABLED=true
    key = poolmanager.GetKeyFromContext(ctx, key)

    // Result: "{tenantId}:idempotency:{scope:key}"

    rds, err := rr.conn.GetClient(ctx)
    return rds.SetNX(ctx, key, value, ttl*time.Second).Result()
}
```

**Key format in multi-tenant mode:**
```
{tenantId}:idempotency:{scope:key}
```

**Defense-in-depth isolation:**
1. **tenantId** - Routes to correct Redis instance/namespace (connection-level, via poolmanager)
2. **scope** - Domain-specific identifiers (data-level, defined by your service)

##### Reverse Key (Both Modes) - Optional

Reverse mapping is optional. Use it when you need to look up the idempotency key from a resource ID.

```go
// IdempotencyReverseKey returns a key for reverse lookups (resourceID → idempotencyKey).
// Format: "idempotency_reverse:{scope}:resourceID"
//
// Examples:
//   - Ledger:  "idempotency_reverse:{organizationID:ledgerID}:transactionID"
//   - CRM:     "idempotency_reverse:{organizationID}:contactID"
func IdempotencyReverseKey(scope, resourceID string) string {
    var builder strings.Builder

    builder.WriteString("idempotency_reverse")
    builder.WriteString(keySeparator)
    builder.WriteString(beginningKey)
    builder.WriteString(scope)
    builder.WriteString(endKey)
    builder.WriteString(keySeparator)
    builder.WriteString(resourceID)

    return builder.String()
}

// Domain-specific helper (midaz example)
func IdempotencyReverseKeyForLedger(organizationID, ledgerID uuid.UUID, transactionID string) string {
    scope := organizationID.String() + ":" + ledgerID.String()
    return IdempotencyReverseKey(scope, transactionID)
}
```

#### 5. Error Code (Service-Specific)

**MUST follow [Error Codes Convention](#error-codes-convention-mandatory)** - use your service prefix.

```go
// pkg/constant/errors.go
const (
    // Use your service prefix (e.g., PLT for Platform, TXN for Transaction, CRM for CRM)
    ErrCodeIdempotencyConflict = "SVC-0084"  // Replace SVC with your service prefix
)

var ErrIdempotencyKey = &BusinessError{
    Code:    ErrCodeIdempotencyConflict,
    Message: "Idempotency key %s is already in use (duplicate in-flight request)",
}

// pkg/errors.go - Error mapping to HTTP response
constant.ErrIdempotencyKey: EntityConflictError{
    Code:  constant.ErrIdempotencyKey.Error(),
    Title: "Duplicate Idempotency Key",
}
```

### Flow Diagram

```
Request → Extract X-Idempotency & X-TTL headers → SHA256(payload) as hash
    ↓
CreateOrCheckIdempotencyKey(scope, key, hash, ttl)
    ↓                        ↑
    │               (scope = domain-specific identifiers)
    │               (e.g., "orgId:ledgerId", "orgId", or "")
    ↓
Build key: IdempotencyInternalKey(scope, key)
    ↓
Redis layer: poolmanager.GetKeyFromContext(ctx, key)
    ↓ (adds {tenantId}: prefix if MULTI_TENANT_ENABLED=true)
Redis SetNX (atomic lock with empty value)
    ├─ Success (lock acquired) → FIRST REQUEST
    │   ├─→ Process operation
    │   ├─→ Async goroutine: SetValueOnExistingIdempotencyKey()
    │   ├─→ Optional: SetIdempotencyMapping() (reverse lookup)
    │   └─→ Return result + X-Idempotency-Replayed: false
    │
    └─ Fail (lock exists) → DUPLICATE REQUEST
        ├─→ Get cached value from same key
        │   ├─→ Value found → Return cached + X-Idempotency-Replayed: true
        │   └─→ No value → Return error SVC-XXXX (in-flight duplicate)
```

### Key Design Decisions (midaz)

| Decision | Rationale |
|----------|-----------|
| **Hash fallback** | If client doesn't provide key, SHA256 of payload ensures natural deduplication |
| **Empty initial value** | SetNX with `""` acts as lock; actual value set asynchronously |
| **Async caching** | `go handler.Command.SetValueOnExistingIdempotencyKey()` - non-blocking |
| **Two-level tenant isolation** | `tenantId` (connection) + domain scope (data) for defense-in-depth |
| **Domain-specific scope** | Scope identifiers depend on your domain (org+ledger, org only, or none) |
| **Poolmanager tenant prefix** | `poolmanager.GetKeyFromContext()` adds tenantId prefix when multi-tenant enabled |
| **Reverse mapping (optional)** | `IdempotencyReverseKey` enables resource lookup by ID when needed |
| **Service-specific error code** | Follows Error Codes Convention with service prefix |

### Which Endpoints Need Idempotency

| Endpoint Type | Idempotency Required | Reason |
|---------------|---------------------|--------|
| POST (create transactions) | ✅ YES | Creates resources, has side effects |
| PUT (replace) | ⚠️ Conditional | If not naturally idempotent |
| PATCH (update) | ⚠️ Conditional | If not naturally idempotent |
| DELETE | ❌ Usually no | Naturally idempotent |
| GET | ❌ No | Read-only, no side effects |

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Our network is reliable" | Networks fail. Retries happen. Always. | **Implement idempotency for all create operations** |
| "Clients won't retry" | HTTP clients auto-retry on timeout. Load balancers retry. | **Assume retries will happen** |
| "Database constraints prevent duplicates" | Constraints cause errors, not graceful handling. | **Return cached success instead of error** |
| "Too complex to implement" | Pattern is standard. Redis SetNX is simple. | **Follow the midaz pattern above** |
| "Only needed for payments" | Any duplicate has cost: support tickets, data cleanup. | **Apply to all resource creation** |
| "We'll add it later" | Retrofitting is harder than building in. | **Implement from the start** |

### Checklist

- [ ] All POST endpoints that create resources have idempotency
- [ ] Using `libConstants.IdempotencyKey`, `libConstants.IdempotencyTTL`, `libConstants.IdempotencyReplayed` from lib-commons
- [ ] Hash fallback implemented (`libCommons.HashSHA256`) for clients without key
- [ ] Redis SetNX used for atomic lock acquisition with empty initial value
- [ ] Cached response returned with `c.Set(libConstants.IdempotencyReplayed, "true")`
- [ ] Error code defined for in-flight duplicates (following Error Codes Convention with service prefix)
- [ ] Key scoping with domain-specific scope (e.g., `IdempotencyInternalKey(scope, key)`)
- [ ] Scope defined based on domain model (org+ledger, org only, tenantId, or none)
- [ ] If multi-tenant enabled: `poolmanager.GetKeyFromContext()` adds tenantId prefix in Redis layer
- [ ] TTL configurable via `X-TTL` header (default from `libRedis.TTL`)
- [ ] Async caching via goroutine (`go handler.Command.SetValueOnExistingIdempotencyKey(...)`)
- [ ] Reverse mapping with `IdempotencyReverseKey` for transaction lookups (if needed)

---

