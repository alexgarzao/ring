# Go Standards - API Patterns

> **Module:** api-patterns.md | **Sections:** §17-21 | **Parent:** [index.md](index.md)

This module covers API naming conventions, pagination patterns, HTTP status codes, OpenAPI documentation, and handler initialization patterns.

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [JSON Naming Convention (camelCase)](#json-naming-convention-camelcase-mandatory) | API response field naming |
| 2 | [Pagination Patterns](#pagination-patterns) | Cursor-based pagination (MANDATORY) |
| 3 | [HTTP Status Code Consistency](#http-status-code-consistency-mandatory) | 201 for creation, 200 for update |
| 4 | [OpenAPI Documentation (Swaggo)](#openapi-documentation-swaggo-mandatory) | Swagger annotations as source of truth |
| 5 | [Handler Constructor Pattern](#handler-constructor-pattern-mandatory) | Dependency injection via constructor |
| 6 | [Input Validation](#input-validation-mandatory) | Request validation at API boundary |

---

## JSON Naming Convention (camelCase) (MANDATORY)

**HARD GATE:** all JSON fields in API requests and responses MUST use `camelCase`. No exceptions.

### Rule

| Layer | Format | Example |
|-------|--------|---------|
| **JSON response fields** | camelCase | `userId`, `createdAt`, `accountBalance` |
| **Pagination response fields** | camelCase | `nextCursor`, `prevCursor`, `hasMore` |
| **Query parameters** | snake_case | `sort_order`, `start_date`, `end_date` |
| **Go structs** | PascalCase | `UserID`, `CreatedAt`, `AccountBalance` |
| **Database columns** | snake_case | `user_id`, `created_at`, `account_balance` |

### Implementation Pattern

```go
// ✅ CORRECT: camelCase in JSON tags
type UserResponse struct {
    ID            string    `json:"id"`
    FirstName     string    `json:"firstName"`
    LastName      string    `json:"lastName"`
    EmailAddress  string    `json:"emailAddress"`
    PhoneNumber   string    `json:"phoneNumber,omitempty"`
    AccountType   string    `json:"accountType"`
    IsActive      bool      `json:"isActive"`
    CreatedAt     time.Time `json:"createdAt"`
    UpdatedAt     time.Time `json:"updatedAt"`
}

// ❌ FORBIDDEN: snake_case in JSON tags
type UserResponse struct {
    ID           string    `json:"id"`
    FirstName    string    `json:"first_name"`     // WRONG
    LastName     string    `json:"last_name"`      // WRONG
    EmailAddress string    `json:"email_address"`  // WRONG
    CreatedAt    time.Time `json:"created_at"`     // WRONG
}
```

### Query Parameters vs Body Fields

**HARD GATE:** Query parameters and body fields use different conventions.

| Location | Convention | Examples |
|----------|------------|----------|
| **Query parameters** | `snake_case` | `?limit=10&sort_order=asc&start_date=2024-01-01` |
| **Request/Response body** | `camelCase` | `{"firstName": "John", "createdAt": "..."}` |

> **Source:** This pattern matches the Midaz API standard (verified via Apidog).

#### Query Parameters (all snake_case)

```go
// ✅ CORRECT: All query params use snake_case
type ListParams struct {
    // Pagination
    Limit     int    `query:"limit"`
    Page      int    `query:"page"`
    Cursor    string `query:"cursor"`
    SortOrder string `query:"sort_order"`

    // Filters
    StartDate string `query:"start_date"`
    EndDate   string `query:"end_date"`
    Status    string `query:"status"`
}
```

```text
✅ CORRECT (all query params snake_case):
GET /v1/users?limit=10&page=1&sort_order=asc&start_date=2024-01-01&end_date=2024-12-31

❌ WRONG (camelCase in query params):
GET /v1/users?limit=10&page=1&sortOrder=asc&startDate=2024-01-01&endDate=2024-12-31
```

#### Response Body - Pagination Fields (snake_case)

```go
// ✅ CORRECT: Pagination response fields use camelCase
type PaginatedResponse struct {
    Items      []interface{} `json:"items"`
    Limit      int           `json:"limit"`
    NextCursor string        `json:"nextCursor,omitempty"`
    PrevCursor string        `json:"prevCursor,omitempty"`
    HasMore    bool          `json:"hasMore"`
}
```

#### Response Body - Data Fields (camelCase)

```go
// ✅ CORRECT: Data fields in body use camelCase
type UserResponse struct {
    ID                   string `json:"id"`
    FirstName            string `json:"firstName"`
    LastName             string `json:"lastName"`
    ParentOrganizationId string `json:"parentOrganizationId"`
    CreatedAt            string `json:"createdAt"`
    UpdatedAt            string `json:"updatedAt"`
}
```

#### Complete List Response Example

```go
// ✅ CORRECT: Full pattern - all response fields use camelCase
type UserListResponse struct {
    // Data fields - camelCase
    Items []struct {
        ID        string `json:"id"`
        FirstName string `json:"firstName"`      // camelCase
        LastName  string `json:"lastName"`       // camelCase
        CreatedAt string `json:"createdAt"`      // camelCase
    } `json:"items"`

    // Pagination fields - camelCase
    Limit      int    `json:"limit"`
    NextCursor string `json:"nextCursor,omitempty"`
    PrevCursor string `json:"prevCursor,omitempty"`
    HasMore    bool   `json:"hasMore"`
}
```

### Common Field Names Reference

**Body Fields (camelCase):**

| Concept | ✅ Correct (camelCase) | ❌ Wrong (snake_case) |
|---------|------------------------|----------------------|
| Identifier | `id`, `userId`, `accountId` | `user_id`, `account_id` |
| Timestamps | `createdAt`, `updatedAt`, `deletedAt` | `created_at`, `updated_at` |
| Status | `isActive`, `isDeleted`, `isVerified` | `is_active`, `is_deleted` |
| Amounts | `totalAmount`, `accountBalance` | `total_amount`, `account_balance` |
| Metadata | `parentId`, `organizationId`, `ledgerId` | `parent_id`, `organization_id` |
| Names | `legalName`, `doingBusinessAs` | `legal_name`, `doing_business_as` |

**Query Parameters (snake_case):**

| Concept | ✅ Correct (snake_case) | ❌ Wrong (camelCase) |
|---------|-------------------------|---------------------|
| Sorting | `sort_order`, `sort_by` | `sortOrder`, `sortBy` |
| Date filters | `start_date`, `end_date` | `startDate`, `endDate` |
| All query params | `snake_case` | `camelCase` |

**Response Fields (camelCase) - Including Pagination:**

| Concept | ✅ Correct (camelCase) | ❌ Wrong (snake_case) |
|---------|------------------------|----------------------|
| Pagination cursors | `nextCursor`, `prevCursor`, `hasMore` | `next_cursor`, `prev_cursor` |
| All response fields | `camelCase` | `snake_case` |

### Detection Commands

```bash
# Find snake_case in JSON response tags (should return 0 matches)
grep -rn 'json:"[a-z]*_[a-z]*' --include="*.go" ./internal

# Check for common violations in body fields (these should NEVER be snake_case)
grep -rn 'json:"created_at\|json:"updated_at\|json:"deleted_at' --include="*.go" ./internal
grep -rn 'json:"first_name\|json:"last_name\|json:"legal_name' --include="*.go" ./internal
grep -rn 'json:"next_cursor\|json:"prev_cursor' --include="*.go" ./internal  # Should be camelCase

# Verify query params ARE snake_case (check query tags)
grep -rn 'query:"[a-zA-Z]*[A-Z]' --include="*.go" ./internal  # Should return 0 (no camelCase in query tags)

# Verify pagination response fields ARE camelCase
grep -rn 'json:"nextCursor\|json:"prevCursor\|json:"hasMore' --include="*.go" ./internal
```

### Anti-Rationalization Table

| Rationalization | Why it's wrong | Required Action |
|-----------------|----------------|-----------------|
| "Database uses snake_case" | DB ≠ API body. Each layer has its convention. | **Use camelCase in JSON body tags** |
| "It's more readable" | Consistency > personal preference. | **Follow the standard** |
| "Existing API uses snake_case in body" | New code must comply. Migrate old APIs. | **Use camelCase for body fields** |
| "OpenAPI spec shows snake_case" | Fix the struct tag, regenerate spec. | **Fix source, run generate-docs** |
| "Query params should match body fields" | No. Query params = snake_case, body = camelCase. Different rules. | **Follow location-based convention** |
| "startDate is cleaner than start_date" | Midaz standard uses snake_case for query params. Follow the standard. | **Use snake_case for query params** |
| "Why two different conventions?" | Industry pattern: URLs use snake_case, JSON uses camelCase. Midaz follows this. | **Accept the dual convention** |

---

## Pagination Patterns

**⛔ HARD GATE:** All list endpoints MUST use **cursor-based pagination**. Offset/page-based pagination is FORBIDDEN due to performance and consistency issues with large datasets.

### Why Cursor-Based Only

| Issue with Offset | Cursor Solution |
|-------------------|-----------------|
| `OFFSET 10000` scans 10k rows before returning | `WHERE id > cursor` uses index directly |
| Data can skip/duplicate if records inserted during navigation | Consistent results regardless of insertions |
| Performance degrades linearly with offset value | Constant performance regardless of position |

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cursor` | string | (none) | Base64-encoded cursor from previous response |
| `limit` | int | 10 | Items per page (max: 100) |
| `sortOrder` | string | "asc" | Sort direction: "asc" or "desc" |
| `startDate` | datetime | (calculated) | Filter start date |
| `endDate` | datetime | now | Filter end date |

### Response Structure (camelCase JSON)

```json
{
  "items": [...],
  "limit": 10,
  "nextCursor": "eyJpZCI6IjEyMzQ1Njc4Li4uIiwicG9pbnRzX25leHQiOnRydWV9",
  "prevCursor": "eyJpZCI6IjEyMzQ1Njc4Li4uIiwicG9pbnRzX25leHQiOmZhbHNlfQ==",
  "hasMore": true
}
```

### Use for All List Endpoints

Transactions, Operations, Balances, Audit logs, Events, Organizations, Ledgers, Assets, Portfolios, Accounts

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cursor` | string | (none) | Base64-encoded cursor from previous response |
| `limit` | int | 10 | Items per page (max: 100) |
| `sort_order` | string | "asc" | Sort direction: "asc" or "desc" |
| `start_date` | datetime | (calculated) | Filter start date |
| `end_date` | datetime | now | Filter end date |

### Handler Implementation

```go
func (h *Handler) GetAllTransactions(c *fiber.Ctx) error {
    ctx := c.UserContext()
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "handler.get_all_transactions")
    defer span.End()

    // Parse and validate query parameters
    headerParams, err := libHTTP.ValidateParameters(c.Queries())
    if err != nil {
        libOpentelemetry.HandleSpanBusinessErrorEvent(&span, "Invalid parameters", err)
        return libHTTP.WithError(c, err)
    }

    // Build pagination request (cursor-based)
    pagination := libPostgres.Pagination{
        Limit:     headerParams.Limit,
        SortOrder: headerParams.SortOrder,
        StartDate: headerParams.StartDate,
        EndDate:   headerParams.EndDate,
    }

    // Query with cursor pagination
    items, cursor, err := h.Query.GetAllTransactions(ctx, orgID, ledgerID, *headerParams)
    if err != nil {
        libOpentelemetry.HandleSpanBusinessErrorEvent(&span, "Query failed", err)
        return libHTTP.WithError(c, err)
    }

    // Set response with cursor
    pagination.SetItems(items)
    pagination.SetCursor(cursor.Next, cursor.Prev)

    return libHTTP.OK(c, pagination)
}
```

**Repository Implementation:**

```go
func (r *Repository) FindAll(ctx context.Context, filter libHTTP.Pagination) ([]Entity, libHTTP.CursorPagination, error) {
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "postgres.find_all")
    defer span.End()

    // Decode cursor if provided
    var decodedCursor libHTTP.Cursor
    isFirstPage := true

    if filter.Cursor != "" {
        isFirstPage = false
        decodedCursor, _ = libHTTP.DecodeCursor(filter.Cursor)
    }

    // Build query with cursor pagination
    query := squirrel.Select("*").From("table_name")
    query, orderUsed := libHTTP.ApplyCursorPagination(
        query,
        decodedCursor,
        strings.ToUpper(filter.SortOrder),
        filter.Limit,
    )

    // Execute query...
    rows, err := query.RunWith(db).QueryContext(ctx)
    // ... scan rows into items ...

    // Check if there are more items
    hasPagination := len(items) > filter.Limit

    // Paginate records (trim to limit, handle direction)
    items = libHTTP.PaginateRecords(
        isFirstPage,
        hasPagination,
        decodedCursor.PointsNext || isFirstPage,
        items,
        filter.Limit,
        orderUsed,
    )

    // Calculate cursors for response
    var firstID, lastID string
    if len(items) > 0 {
        firstID = items[0].ID
        lastID = items[len(items)-1].ID
    }

    cursor, _ := libHTTP.CalculateCursor(
        isFirstPage,
        hasPagination,
        decodedCursor.PointsNext || isFirstPage,
        firstID,
        lastID,
    )

    return items, cursor, nil
}
```

---

### Shared Utilities from lib-commons

| Utility | Package | Purpose |
|---------|---------|---------|
| `Pagination` struct | `lib-commons/commons/postgres` | Unified response structure |
| `Cursor` struct | `lib-commons/commons/net/http` | Cursor encoding |
| `DecodeCursor` | `lib-commons/commons/net/http` | Parse cursor from request |
| `ApplyCursorPagination` | `lib-commons/commons/net/http` | Add cursor to SQL query |
| `PaginateRecords` | `lib-commons/commons/net/http` | Trim results, handle direction |
| `CalculateCursor` | `lib-commons/commons/net/http` | Generate next/prev cursors |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_PAGINATION_LIMIT` | 100 | Maximum allowed limit per request |
| `MAX_PAGINATION_MONTH_DATE_RANGE` | 1 | Default date range in months |

---

## HTTP Status Code Consistency (MANDATORY)

Swagger annotations with inconsistent response codes (using 200 OK for resource creation instead of 201 Created) break API contracts and client expectations.

**⛔ HARD GATE:** HTTP status codes MUST match the operation semantics. Using incorrect status codes breaks API contracts and client expectations.

### Status Code Rules

| Operation | HTTP Method | ✅ Correct Status | ❌ Wrong Status | Description |
|-----------|-------------|-------------------|-----------------|-------------|
| Create resource | POST | `201 Created` | 200 OK | New resource created |
| Update resource | PUT/PATCH | `200 OK` | 201 Created | Existing resource modified |
| Delete resource | DELETE | `204 No Content` | 200 OK | Resource removed |
| Get resource | GET | `200 OK` | - | Resource retrieved |
| List resources | GET | `200 OK` | - | Collection retrieved |
| Action endpoint | POST | `200 OK` or `202 Accepted` | 201 Created | Action performed (no resource created) |

### Correct Swagger Annotations

```go
// ✅ CORRECT: 201 Created for POST that creates a resource
// @Summary      Create a new user
// @Success      201            {object}  mmodel.User  "Successfully created user"
// @Router       /v1/users [post]
func (h *Handler) CreateUser(c *fiber.Ctx) error {
    // ... create user ...
    return libHTTP.Created(c, user)  // Returns 201
}

// ✅ CORRECT: 200 OK for PUT that updates a resource
// @Summary      Update user
// @Success      200            {object}  mmodel.User  "Successfully updated user"
// @Router       /v1/users/{id} [put]
func (h *Handler) UpdateUser(c *fiber.Ctx) error {
    // ... update user ...
    return libHTTP.OK(c, user)  // Returns 200
}

// ✅ CORRECT: 204 No Content for DELETE
// @Summary      Delete user
// @Success      204            "Successfully deleted user"
// @Router       /v1/users/{id} [delete]
func (h *Handler) DeleteUser(c *fiber.Ctx) error {
    // ... delete user ...
    return libHTTP.NoContent(c)  // Returns 204
}
```

### FORBIDDEN Patterns

```go
// ❌ FORBIDDEN: 200 OK for resource creation
// @Summary      Create a new user
// @Success      200            {object}  mmodel.User  "Successfully created user"  // WRONG: Should be 201
// @Router       /v1/users [post]

// ❌ FORBIDDEN: 201 Created for update
// @Summary      Update user
// @Success      201            {object}  mmodel.User  "Successfully updated user"  // WRONG: Should be 200
// @Router       /v1/users/{id} [put]

// ❌ FORBIDDEN: Mismatched annotation and implementation
// @Success      201            {object}  mmodel.User
// @Router       /v1/users [post]
func (h *Handler) CreateUser(c *fiber.Ctx) error {
    return libHTTP.OK(c, user)  // WRONG: Returns 200, annotation says 201
}
```

### lib-commons Response Methods

| Method | Status Code | Use For |
|--------|-------------|---------|
| `libHTTP.Created(c, data)` | 201 | POST creating a new resource |
| `libHTTP.OK(c, data)` | 200 | GET, PUT, PATCH, action POSTs |
| `libHTTP.NoContent(c)` | 204 | DELETE, successful operations without body |
| `libHTTP.Accepted(c, data)` | 202 | Async operations (will be processed later) |

### Detection Commands (MANDATORY)

```bash
# MANDATORY: Run before every PR with API changes
# Find 200 OK used for POST creation endpoints
grep -B 10 "@Router.*\[post\]" internal/adapters/http/in/*.go | grep "@Success.*200"

# Find 201 Created used for PUT/PATCH endpoints (use -E for alternation)
grep -E -B 10 "@Router.*\[(put|patch)\]" internal/adapters/http/in/*.go | grep "@Success.*201"

# Expected: Both commands return 0 matches
# If matches found: Fix annotation to use correct status code
```

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "200 OK is simpler" | Clients expect 201 for creation. Breaking convention breaks clients. | **Use 201 for POST creation** |
| "Both mean success" | Different semantics: 201 = created, 200 = retrieved/updated. | **Use correct code for operation** |
| "Frontend ignores status" | Frontend SHOULD check status. API MUST be correct. | **Use correct status code** |
| "OpenAPI just documents" | OpenAPI is a contract. Wrong docs = broken contract. | **Match annotation to implementation** |
| "We've always used 200" | Legacy is not justification. Fix during maintenance. | **Correct when modifying endpoint** |

---

## OpenAPI Documentation (Swaggo) (MANDATORY)

**HARD GATE:** All API documentation MUST be generated from code annotations using swaggo. Editing generated files directly is FORBIDDEN.

### Source of Truth

| Source | Editable | Purpose |
|--------|----------|---------|
| **Handler annotations** (`@Summary`, `@Param`, etc.) | ✅ YES | Define endpoint documentation |
| **main.go annotations** (`@title`, `@version`, etc.) | ✅ YES | Define API metadata |
| `api/swagger.json` | ❌ NO | **GENERATED** - Do not edit |
| `api/swagger.yaml` | ❌ NO | **GENERATED** - Do not edit |
| `api/docs.go` | ❌ NO | **GENERATED** - Do not edit |

### Required Tool

| Tool | Installation | Purpose |
|------|--------------|---------|
| `swaggo/swag` | `go install github.com/swaggo/swag/cmd/swag@latest` | Generate OpenAPI specs from annotations |

### FORBIDDEN: Editing Generated Files

```yaml
# ❌ FORBIDDEN: Directly editing api/swagger.yaml
paths:
  /v1/users:
    get:
      summary: "Get all users"  # DON'T edit here!
```

```go
// ✅ CORRECT: Edit the annotation in the handler
// @Summary      Get all users
// @Description  Retrieve a paginated list of all users
// @Tags         Users
// @Router       /v1/users [get]
func (h *Handler) GetAllUsers(c *fiber.Ctx) error {
```

**Why this matters:**
- Generated files are overwritten on each `swag init`
- Manual edits are lost and cause confusion
- Annotations are version-controlled with the code
- Single source of truth prevents drift

### API Metadata (main.go)

Add these annotations above your `main()` function:

```go
// @title           Service Name API
// @version         v1.0.0
// @description     Brief description of this service API.

// @termsOfService  http://swagger.io/terms/
// @contact.name    Discord community
// @contact.url     https://discord.gg/DnhqKwkGv3

// @license.name    Apache 2.0
// @license.url     http://www.apache.org/licenses/LICENSE-2.0.html

// @host            localhost:3000
// @BasePath        /

func main() {
    // ...
}
```

### Handler Annotations (Complete Reference)

MUST: every handler function has swaggo annotations:

```go
// CreateUser creates a new user
// @Summary      Create a new user
// @Description  Create a new user with the provided information
// @Tags         Users
// @Accept       json
// @Produce      json
// @Param        Authorization  header    string                 true  "Authorization Bearer Token"
// @Param        X-Request-Id   header    string                 false "Request ID for tracing"
// @Param        user           body      mmodel.CreateUserInput true  "User creation payload"
// @Success      201            {object}  mmodel.User            "Successfully created user"
// @Failure      400            {object}  mmodel.Error           "Invalid input, validation errors"
// @Failure      401            {object}  mmodel.Error           "Unauthorized access"
// @Failure      403            {object}  mmodel.Error           "Forbidden access"
// @Failure      409            {object}  mmodel.Error           "Conflict: User already exists"
// @Failure      500            {object}  mmodel.Error           "Internal server error"
// @Router       /v1/users [post]
func (h *Handler) CreateUser(c *fiber.Ctx) error {
    // implementation
}
```

### Annotation Reference Table

| Annotation | Required | Description | Example |
|------------|----------|-------------|---------|
| `@Summary` | ✅ | Short description (shown in list) | `@Summary Create a new user` |
| `@Description` | ✅ | Detailed description | `@Description Create a new user with validation` |
| `@Tags` | ✅ | Group endpoints by resource | `@Tags Users` |
| `@Accept` | For POST/PUT/PATCH | Request content type | `@Accept json` |
| `@Produce` | ✅ | Response content type | `@Produce json` |
| `@Param` | Per parameter | Define each parameter | See below |
| `@Success` | ✅ | Success response | `@Success 200 {object} User` |
| `@Failure` | ✅ | Error responses (all expected) | `@Failure 400 {object} Error` |
| `@Router` | ✅ | Endpoint path and method | `@Router /v1/users [get]` |

### @Param Syntax

```text
@Param  name  location  type  required  "description"

Locations: path, query, header, body, formData
Types: string, int, bool, object (for body)
Required: true, false
```

**Examples:**

```go
// Path parameter
// @Param  id  path  string  true  "User ID (UUID format)"

// Query parameter
// @Param  page   query  int     false  "Page number (default: 1)"
// @Param  limit  query  int     false  "Items per page (default: 10, max: 100)"

// Header parameter
// @Param  Authorization  header  string  true   "Authorization Bearer Token"
// @Param  X-Request-Id   header  string  false  "Request ID for tracing"

// Body parameter
// @Param  user  body  mmodel.CreateUserInput  true  "User creation payload"
```

### Required Failure Responses

MUST document these failure responses for every endpoint:

| Status | When | Annotation |
|--------|------|------------|
| 400 | Invalid input/validation | `@Failure 400 {object} mmodel.Error "Invalid input"` |
| 401 | Missing/invalid auth | `@Failure 401 {object} mmodel.Error "Unauthorized"` |
| 403 | Insufficient permissions | `@Failure 403 {object} mmodel.Error "Forbidden"` |
| 404 | Resource not found (for GET/PUT/DELETE by ID) | `@Failure 404 {object} mmodel.Error "Not found"` |
| 409 | Conflict (for POST creating duplicates) | `@Failure 409 {object} mmodel.Error "Conflict"` |
| 500 | Internal error | `@Failure 500 {object} mmodel.Error "Internal error"` |

### Generation Command

**See [devops.md - Documentation Commands](../devops.md#documentation-commands-mandatory)** for the complete Makefile implementation.

**Quick reference:**

| Command | Purpose |
|---------|---------|
| `make generate-docs` | Generate Swagger from annotations |
| `make dev-setup` | Install swag and other tools |

**swag init parameters:**

| Flag | Purpose |
|------|---------|
| `-g cmd/app/main.go` | Entry point with API metadata |
| `-o api` | Output directory |
| `--parseDependency` | Parse external dependencies for models |
| `--parseInternal` | Parse internal packages |

### Generated Files Structure

```text
/api
  docs.go         # Go code for embedding (GENERATED)
  swagger.json    # OpenAPI spec in JSON (GENERATED)
  swagger.yaml    # OpenAPI spec in YAML (GENERATED)
```

### Workflow for OpenAPI Changes

```text
1. Receive CodeRabbit issue about OpenAPI spec
2. Identify which handler needs the change
3. Edit the ANNOTATION in the handler Go file
4. Run: make generate-docs
5. Commit BOTH: handler change + regenerated api/ files
6. Verify the spec change in swagger.yaml
```

### Anti-Patterns (FORBIDDEN)

```go
// ❌ FORBIDDEN: Handler without annotations
func (h *Handler) GetUser(c *fiber.Ctx) error {
    // No swaggo annotations = undocumented endpoint
}

// ❌ FORBIDDEN: Missing required failure responses
// @Success 200 {object} User
// @Router  /v1/users/{id} [get]
// Missing: @Failure 400, 401, 403, 404, 500

// ❌ FORBIDDEN: Vague descriptions
// @Summary Get user
// @Description Get user
// Should be: @Description Retrieve a user by their unique identifier (UUID)
```

### Detection Commands

```bash
# Find handlers without @Router annotation (undocumented)
grep -rn "func.*Handler.*fiber.Ctx" --include="*.go" ./internal/adapters/http | \
  while read line; do
    file=$(echo "$line" | cut -d: -f1)
    linenum=$(echo "$line" | cut -d: -f2)
    if ! head -n "$linenum" "$file" | tail -20 | grep -q "@Router"; then
      echo "Missing @Router: $line"
    fi
  done

# Verify api/ files are in sync (should show no diff after generate-docs)
make generate-docs && git diff --exit-code api/
```

### Anti-Rationalization Table

| Rationalization | Why it's wrong | Required Action |
|-----------------|----------------|-----------------|
| "Editing YAML is faster" | Edits are lost on next generation. Causes drift. | **Edit annotations, run generate-docs** |
| "The annotation is verbose" | Verbosity ensures complete documentation. | **Write complete annotations** |
| "I'll add annotations later" | Later = never. Undocumented APIs are incomplete. | **Add annotations with the handler** |
| "Only public APIs need docs" | All APIs need docs for internal developers too. | **Document all endpoints** |
| "CodeRabbit can fix the YAML directly" | YAML is generated. Fix the source (annotations). | **Edit handler annotations** |

---

## Handler Constructor Pattern (MANDATORY)

Handlers with implicit dependencies make testing difficult and hide coupling. Direct struct initialization bypasses validation.

**⛔ HARD GATE:** All HTTP handlers MUST use constructor functions for initialization. Direct struct initialization is FORBIDDEN.

### Why Constructor Pattern Is MANDATORY

| Problem | Without Constructor | With Constructor |
|---------|---------------------|------------------|
| Dependency visibility | Hidden in struct | Explicit in signature |
| Nil checks | Scattered in methods | Single place in constructor |
| Testing | Mock injection difficult | Clean dependency injection |
| Compilation safety | Runtime nil panics | Compile-time errors |

### Handler Constructor Pattern

```go
// internal/adapters/http/in/user_handler.go

// Handler struct holds dependencies (private fields)
type UserHandler struct {
    command *command.UseCase
    query   *query.UseCase
    logger  libLog.Logger
}

// NewUserHandler creates a handler with validated dependencies
// MANDATORY: Constructor validates all dependencies; returns error instead of panicking
func NewUserHandler(cmd *command.UseCase, qry *query.UseCase, logger libLog.Logger) (*UserHandler, error) {
    if cmd == nil {
        return nil, fmt.Errorf("command use case is required")
    }
    if qry == nil {
        return nil, fmt.Errorf("query use case is required")
    }
    if logger == nil {
        return nil, fmt.Errorf("logger is required")
    }

    return &UserHandler{
        command: cmd,
        query:   qry,
        logger:  logger,
    }, nil
}

// Handler methods use injected dependencies
func (h *UserHandler) CreateUser(c *fiber.Ctx) error {
    // h.command, h.query, h.logger are guaranteed non-nil
    // ...
}
```

### Bootstrap Integration (REQUIRED)

```go
// internal/bootstrap/config.go

func InitServers() (*Service, error) {
    // ... initialize dependencies ...

    // CORRECT: Use constructor and handle error
    userHandler, err := httpin.NewUserHandler(commandUseCase, queryUseCase, logger)
    if err != nil {
        return nil, fmt.Errorf("create user handler: %w", err)
    }

    // Pass handler to router
    httpApp := httpin.NewRouter(logger, telemetry, userHandler)

    // ...
    return &Service{httpApp: httpApp}, nil
}
```

### FORBIDDEN Patterns

```go
// ❌ FORBIDDEN: Direct struct initialization
userHandler := &httpin.UserHandler{
    Command: commandUseCase,  // No validation
    Query:   queryUseCase,
    Logger:  logger,
}

// ❌ FORBIDDEN: Public fields allowing direct access
type UserHandler struct {
    Command *command.UseCase  // WRONG: Public field
    Query   *query.UseCase    // WRONG: Public field
}

// ❌ FORBIDDEN: Constructor without validation
func NewUserHandler(cmd *command.UseCase) *UserHandler {
    return &UserHandler{command: cmd}  // WRONG: No nil check
}

// ❌ FORBIDDEN: Lazy initialization in handler methods
func (h *UserHandler) CreateUser(c *fiber.Ctx) error {
    if h.command == nil {  // WRONG: Should fail at startup, not request time
        return errors.New("not initialized")
    }
}
```

### Detection Commands (MANDATORY)

```bash
# MANDATORY: Run before every PR that adds/modifies handlers
# Find handlers without constructor functions
for f in internal/adapters/http/in/*_handler.go; do
  handler=$(basename "$f" .go | sed 's/_handler//')
  if ! grep -q "func New.*Handler" "$f" 2>/dev/null; then
    echo "MISSING CONSTRUCTOR: $f"
  fi
done

# Find direct struct initialization of handlers (potential violation)
grep -rn "&.*Handler{" internal/bootstrap --include="*.go" | grep -v "New.*Handler"

# Find handlers with public fields (violation)
grep -rn "type.*Handler struct" internal/adapters/http/in --include="*.go" -A 10 | \
  grep -E "^\s+[A-Z][a-zA-Z]*\s+\*?[a-zA-Z]+"

# Expected: All handlers have New* constructor, no direct initialization, no public fields
# If any violation found: STOP. Fix before proceeding.
```

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Direct initialization is simpler" | Simplicity now = nil panics later. | **Use constructor** |
| "I'll add validation later" | Later = production incident. Fail fast at startup. | **Add validation in constructor** |
| "Tests can set fields directly" | Tests should use same constructor as production. | **Use constructor in tests too** |
| "Handler is small, doesn't need it" | Consistency matters more than size. | **Use constructor for all handlers** |
| "Public fields are easier to access" | Easier access = easier to corrupt. | **Use private fields + constructor** |

---

## Input Validation (MANDATORY)

**⛔ HARD GATE:** All user input MUST be validated at the API boundary before processing. Trusting user input is FORBIDDEN.

### Defense in Depth Principle

Validate at EVERY layer where data enters the system:

```text
┌─────────────────────────────────────────────────────────────────┐
│ HTTP Request                                                     │
│   ↓                                                              │
│ [Layer 1: Handler] - Struct binding + validation tags            │
│   ↓                                                              │
│ [Layer 2: Use Case] - Business rule validation                   │
│   ↓                                                              │
│ [Layer 3: Domain] - Domain invariant validation                  │
│   ↓                                                              │
│ [Layer 4: Repository] - Database constraints                     │
└─────────────────────────────────────────────────────────────────┘
```

### Required Validation at Handler Layer

**MANDATORY: Use go-playground/validator v10 with struct tags.**

```go
import (
    "github.com/go-playground/validator/v10"
)

// ✅ CORRECT: Input struct with validation tags
type CreateUserInput struct {
    Email     string `json:"email" validate:"required,email,max=255"`
    FirstName string `json:"firstName" validate:"required,min=1,max=100"`
    LastName  string `json:"lastName" validate:"required,min=1,max=100"`
    Age       int    `json:"age" validate:"omitempty,gte=0,lte=150"`
    Role      string `json:"role" validate:"required,oneof=admin user guest"`
    Phone     string `json:"phone" validate:"omitempty,e164"`
}

// Handler validates input before processing
func (h *Handler) CreateUser(c *fiber.Ctx) error {
    ctx := c.UserContext()

    var input CreateUserInput
    if err := c.BodyParser(&input); err != nil {
        return libHTTP.WithError(c, ErrInvalidJSON)
    }

    // ✅ CORRECT: Validate before processing
    if err := h.validator.Struct(input); err != nil {
        return libHTTP.WithError(c, translateValidationError(err))
    }

    // Now input is validated, proceed with business logic
    result, err := h.command.CreateUser(ctx, input)
    // ...
}
```

### Common Validation Tags Reference

| Tag | Description | Example |
|-----|-------------|---------|
| `required` | Field must be present and non-zero | `validate:"required"` |
| `email` | Valid email format | `validate:"email"` |
| `uuid` | Valid UUID format | `validate:"uuid"` |
| `min` | Minimum length (string) or value (number) | `validate:"min=1"` |
| `max` | Maximum length (string) or value (number) | `validate:"max=255"` |
| `gte` | Greater than or equal | `validate:"gte=0"` |
| `lte` | Less than or equal | `validate:"lte=100"` |
| `oneof` | Value must be one of listed | `validate:"oneof=active inactive"` |
| `e164` | International phone format | `validate:"e164"` |
| `url` | Valid URL format | `validate:"url"` |
| `iso8601` | Valid ISO8601 date | `validate:"iso8601"` |

### Validation Error Translation

```go
// ✅ CORRECT: Translate validation errors to user-friendly messages
func translateValidationError(err error) error {
    var validationErrors validator.ValidationErrors
    if errors.As(err, &validationErrors) {
        var errMessages []string
        for _, e := range validationErrors {
            errMessages = append(errMessages, formatFieldError(e))
        }
        return NewValidationError(errMessages)
    }
    return ErrInvalidInput
}

func formatFieldError(e validator.FieldError) string {
    switch e.Tag() {
    case "required":
        return fmt.Sprintf("field '%s' is required", e.Field())
    case "email":
        return fmt.Sprintf("field '%s' must be a valid email", e.Field())
    case "min":
        return fmt.Sprintf("field '%s' must be at least %s characters", e.Field(), e.Param())
    case "max":
        return fmt.Sprintf("field '%s' must be at most %s characters", e.Field(), e.Param())
    case "oneof":
        return fmt.Sprintf("field '%s' must be one of: %s", e.Field(), e.Param())
    default:
        return fmt.Sprintf("field '%s' failed validation: %s", e.Field(), e.Tag())
    }
}
```

### UUID and Path Parameter Validation

```go
// ✅ CORRECT: Validate path parameters
func (h *Handler) GetUser(c *fiber.Ctx) error {
    userID := c.Params("id")

    // Validate UUID format
    if _, err := uuid.Parse(userID); err != nil {
        return libHTTP.WithError(c, ErrInvalidUserID)
    }

    // Proceed with validated ID
    user, err := h.query.GetUser(ctx, userID)
    // ...
}
```

### Query Parameter Validation

```go
// ✅ CORRECT: Validate query parameters with defaults
func (h *Handler) ListUsers(c *fiber.Ctx) error {
    // Use lib-commons validation
    params, err := libHTTP.ValidateParameters(c.Queries())
    if err != nil {
        return libHTTP.WithError(c, err)
    }

    // params.Limit, params.Page are validated and have defaults
    // ...
}
```

### FORBIDDEN Patterns

```go
// ❌ FORBIDDEN: Trusting input without validation
func (h *Handler) CreateUser(c *fiber.Ctx) error {
    var input CreateUserInput
    c.BodyParser(&input)
    // WRONG: Using input directly without validation
    h.command.CreateUser(ctx, input)
}

// ❌ FORBIDDEN: Validating only some fields
type CreateUserInput struct {
    Email string `json:"email" validate:"required,email"`
    Name  string `json:"name"`  // WRONG: No validation on required field
}

// ❌ FORBIDDEN: Catching validation errors but not returning them
if err := h.validator.Struct(input); err != nil {
    log.Error(err)
    // WRONG: Continuing despite validation failure
}

// ❌ FORBIDDEN: Manual validation when tags would suffice
if input.Email == "" {
    return ErrEmailRequired  // WRONG: Use validate:"required" tag
}
if len(input.Name) > 100 {
    return ErrNameTooLong  // WRONG: Use validate:"max=100" tag
}
```

### Detection Commands (MANDATORY)

```bash
# MANDATORY: Run before every PR with API changes

# Find input structs without validation tags
grep -rn "type.*Input struct" internal/adapters/http --include="*.go" -A 10 | \
  grep -v "validate:" | grep "json:"

# Find handlers that use BodyParser without validation
grep -rn "BodyParser" internal/adapters/http --include="*.go" -A 5 | \
  grep -v "validator\|Validate\|validate"

# Find path parameter usage without UUID validation
grep -rn 'Params("id")' internal/adapters/http --include="*.go" -A 3 | \
  grep -v "uuid.Parse\|ValidateUUID"

# Expected: 0 matches for unvalidated inputs
# If matches found: Add validation before processing
```

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Frontend validates input" | Frontend can be bypassed. Server is last defense. | **Validate on server** |
| "Input comes from trusted service" | Services can be compromised. Trust nothing. | **Validate all input** |
| "Validation is expensive" | Invalid data processing is more expensive. Fail fast. | **Validate early** |
| "Database will reject invalid data" | Database errors are cryptic. Validate for clear messages. | **Validate before DB** |
| "Small internal API doesn't need it" | Internal APIs become external. Build right from start. | **Validate all APIs** |
| "Manual validation is clearer" | Tags are declarative and consistent. Manual is error-prone. | **Use validation tags** |

---
