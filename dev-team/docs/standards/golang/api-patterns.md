# Go Standards - API Patterns

> **Module:** api-patterns.md | **Sections:** §17-19 | **Parent:** [index.md](index.md)

This module covers API naming conventions, pagination patterns, and OpenAPI documentation.

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [JSON Naming Convention (camelCase)](#json-naming-convention-camelcase-mandatory) | API response field naming |
| 2 | [Pagination Patterns](#pagination-patterns) | Cursor-based and page-based pagination implementation |
| 3 | [OpenAPI Documentation (Swaggo)](#openapi-documentation-swaggo-mandatory) | Swagger annotations as source of truth |

---

## JSON Naming Convention (camelCase) (MANDATORY)

**HARD GATE:** All JSON data fields in API requests and responses MUST use `camelCase`.

**EXCEPTION:** Pagination metadata fields use `snake_case` (see "Query Parameters vs Body Fields" below).

### Rule

| Layer | Format | Example | Exception |
|-------|--------|---------|-----------|
| **JSON data fields** | camelCase | `userId`, `createdAt`, `accountBalance` | - |
| **Pagination metadata** | snake_case | `limit`, `next_cursor`, `prev_cursor` | Midaz standard |
| **Go structs** | PascalCase | `UserID`, `CreatedAt`, `AccountBalance` | - |
| **Database** | snake_case | `user_id`, `created_at`, `account_balance` | - |

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

**HARD GATE:** Query parameters and body fields use DIFFERENT conventions.

| Location | Convention | Examples |
|----------|------------|----------|
| **Query parameters** | `snake_case` | `?limit=10&sort_order=asc&start_date=2024-01-01` |
| **Request/Response body** | `camelCase` | `{"firstName": "John", "createdAt": "..."}` |

> **Source:** This pattern matches the Midaz API standard (verified via Apidog).

#### Query Parameters (ALL snake_case)

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
// ✅ CORRECT: Pagination response fields use snake_case
type PaginatedResponse struct {
    Items      []interface{} `json:"items"`
    Limit      int           `json:"limit"`
    Page       int           `json:"page"`
    NextCursor string        `json:"next_cursor,omitempty"`
    PrevCursor string        `json:"prev_cursor,omitempty"`
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
// ✅ CORRECT: Full pattern - pagination (snake_case) + data (camelCase)
type UserListResponse struct {
    // Data fields - camelCase
    Items []struct {
        ID        string `json:"id"`
        FirstName string `json:"firstName"`      // camelCase
        LastName  string `json:"lastName"`       // camelCase
        CreatedAt string `json:"createdAt"`      // camelCase
    } `json:"items"`

    // Pagination fields - snake_case
    Limit      int    `json:"limit"`
    Page       int    `json:"page"`
    NextCursor string `json:"next_cursor,omitempty"`
    PrevCursor string `json:"prev_cursor,omitempty"`
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

**Query Parameters & Pagination Response (snake_case):**

| Concept | ✅ Correct (snake_case) | ❌ Wrong (camelCase) |
|---------|-------------------------|---------------------|
| Pagination | `limit`, `page`, `cursor`, `next_cursor`, `prev_cursor` | `nextCursor`, `prevCursor` |
| Sorting | `sort_order`, `sort_by` | `sortOrder`, `sortBy` |
| Date filters | `start_date`, `end_date` | `startDate`, `endDate` |
| All query params | `snake_case` | `camelCase` |

### Detection Commands

```bash
# Find snake_case in JSON body tags (exclude pagination response fields)
# Should return 0 matches for data fields
grep -rn 'json:"[a-z]*_[a-z]*' --include="*.go" ./internal | grep -v "next_cursor\|prev_cursor\|sort_order\|start_date\|end_date"

# Check for common violations in body fields (these should NEVER be snake_case)
grep -rn 'json:"created_at\|json:"updated_at\|json:"deleted_at' --include="*.go" ./internal
grep -rn 'json:"first_name\|json:"last_name\|json:"legal_name' --include="*.go" ./internal
grep -rn 'json:"[a-z]*_id"' --include="*.go" ./internal

# Verify query params ARE snake_case (check query tags)
grep -rn 'query:"[a-zA-Z]*[A-Z]' --include="*.go" ./internal  # Should return 0 (no camelCase in query tags)

# Verify pagination response fields ARE snake_case
grep -rn 'json:"next_cursor\|json:"prev_cursor' --include="*.go" ./internal
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

Lerian Studio supports multiple pagination patterns. This section provides **implementation details** for each pattern.

> **Note**: The pagination strategy should be decided during the **TRD (Technical Requirements Document)** phase, not during implementation. See the `ring:pre-dev-trd-creation` skill for the decision workflow. If no TRD exists, consult with the user before implementing.

### Quick Reference

| Pattern | Best For | Query Params | Response Fields |
|---------|----------|--------------|-----------------|
| Cursor-Based | High-volume data, real-time | `cursor`, `limit`, `sort_order` | `next_cursor`, `prev_cursor` |
| Page-Based | Low-volume data | `page`, `limit`, `sort_order` | `page`, `limit` |
| Page-Based + Total | UI needs "Page X of Y" | `page`, `limit`, `sort_order` | `page`, `limit`, `total` |

### Decision Guide (Reference Only)

```
Is this a high-volume entity (>10k records typical)?
├── YES → Use Cursor-Based Pagination
└── no  → Use Page-Based Pagination

Does the user need to jump to arbitrary pages?
├── YES → Use Page-Based Pagination
└── no  → Cursor-Based is fine

Does the UI need to show total count (e.g., "Page 1 of 10")?
├── YES → Use Page-Based with Total Count
└── no  → Standard Page-Based is sufficient
```

---

### Pattern 1: Cursor-Based Pagination (PREFERRED for high-volume)

Use for: Transactions, Operations, Balances, Audit logs, Events

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cursor` | string | (none) | Base64-encoded cursor from previous response |
| `limit` | int | 10 | Items per page (max: 100) |
| `sort_order` | string | "asc" | Sort direction: "asc" or "desc" |
| `start_date` | datetime | (calculated) | Filter start date |
| `end_date` | datetime | now | Filter end date |

**Response Structure:**

```json
{
  "items": [...],
  "limit": 10,
  "next_cursor": "eyJpZCI6IjEyMzQ1Njc4Li4uIiwicG9pbnRzX25leHQiOnRydWV9",
  "prev_cursor": "eyJpZCI6IjEyMzQ1Njc4Li4uIiwicG9pbnRzX25leHQiOmZhbHNlfQ=="
}
```

**Handler Implementation:**

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

### Pattern 2: Page-Based (Offset) Pagination

Use for: Organizations, Ledgers, Assets, Portfolios, Accounts

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number (1-indexed) |
| `limit` | int | 10 | Items per page (max: 100) |
| `sort_order` | string | "asc" | Sort direction |
| `start_date` | datetime | (calculated) | Filter start date |
| `end_date` | datetime | now | Filter end date |

**Response Structure:**

```json
{
  "items": [...],
  "page": 1,
  "limit": 10
}
```

**Handler Implementation:**

```go
func (h *Handler) GetAllOrganizations(c *fiber.Ctx) error {
    ctx := c.UserContext()
    logger, tracer, _, _ := libCommons.NewTrackingFromContext(ctx)

    ctx, span := tracer.Start(ctx, "handler.get_all_organizations")
    defer span.End()

    headerParams, err := libHTTP.ValidateParameters(c.Queries())
    if err != nil {
        return libHTTP.WithError(c, err)
    }

    // Build page-based pagination
    pagination := libPostgres.Pagination{
        Limit:     headerParams.Limit,
        Page:      headerParams.Page,
        SortOrder: headerParams.SortOrder,
        StartDate: headerParams.StartDate,
        EndDate:   headerParams.EndDate,
    }

    // Query with offset pagination (uses ToOffsetPagination())
    items, err := h.Query.GetAllOrganizations(ctx, headerParams.ToOffsetPagination())
    if err != nil {
        return libHTTP.WithError(c, err)
    }

    pagination.SetItems(items)

    return libHTTP.OK(c, pagination)
}
```

**Repository Implementation:**

```go
func (r *Repository) FindAll(ctx context.Context, pagination http.Pagination) ([]Entity, error) {
    offset := (pagination.Page - 1) * pagination.Limit

    query := squirrel.Select("*").
        From("table_name").
        OrderBy("id " + pagination.SortOrder).
        Limit(uint64(pagination.Limit)).
        Offset(uint64(offset))

    // Execute query...
    return items, nil
}
```

---

### Pattern 3: Page-Based with Total Count

Use when: Client needs total count for pagination UI (showing "Page 1 of 10")

**Response Structure:**

```json
{
  "items": [...],
  "page": 1,
  "limit": 10,
  "total": 100
}
```

**Note:** Adds a COUNT query overhead. Only use if total is required.

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

Every handler function MUST have swaggo annotations:

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

Every endpoint MUST document these failure responses:

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

