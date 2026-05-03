---
name: ring:write-api
description: |
  Patterns and structure for writing API reference documentation including
  endpoint descriptions, request/response schemas, and error documentation.

trigger: |
  - Documenting REST API endpoints
  - Writing request/response examples
  - Documenting error codes
  - Creating API field descriptions

skip_when: |
  - Writing conceptual guides → use write-guide
  - Reviewing documentation → use review-docs
  - Writing code → use dev-team agents

sequence:
  before: [review-docs]

related:
  similar: [write-guide]
  complementary: [documentation-structure]
---

# Writing API Reference Documentation

API reference documents what each endpoint does, its parameters, request/response formats, and error conditions. Focus on the "what" not the "why."

## API Reference Principles

- **RESTful and Predictable:** Standard HTTP methods, consistent URL patterns, idempotency documented
- **Consistent Formats:** JSON requests/responses, clear typing, standard error format
- **Explicit Versioning:** Version in URL path, backward compatibility notes, deprecated fields marked

## Endpoint Documentation Structure

| Section | Content |
|---------|---------|
| **Title** | Endpoint name |
| **Description** | What the endpoint does |
| **HTTP Method + Path** | `POST /v1/organizations/{orgId}/ledgers/{ledgerId}/accounts` |
| **Path Parameters** | Table: Parameter, Type, Required, Description |
| **Query Parameters** | Table: Parameter, Type, Default, Description |
| **Request Body** | JSON example + fields table |
| **Success Response** | Status code + JSON example + fields table |
| **Errors** | Table: Status Code, Error Code, Description |

## Field Descriptions

Every field needs: purpose, type, required (request only), constraints, example.

| Type | Pattern | Example |
|------|---------|---------|
| UUID | "The unique identifier of the [Entity]" | `id: uuid — The unique identifier of the Account` |
| String | "[Purpose] (constraints)" | `code: string — Asset code (max 10 chars, uppercase, e.g., "BRL")` |
| Enum | "[Purpose]: `val1`, `val2`, `val3`" | `type: enum — Asset type: \`currency\`, \`crypto\`, \`commodity\`` |
| Boolean | "If `true`, [what happens]. Default: `[value]`" | `allowSending: boolean — If \`true\`, sending permitted. Default: \`true\`` |
| Integer | "[Purpose] (range)" | `scale: integer — Decimal places (0-18)` |
| Timestamp | "Timestamp of [event] (UTC)" | `createdAt: timestamptz — Timestamp of creation (UTC)` |
| Array | "List of [what it contains]" | `operations: array — List of operations in the transaction` |

## Request/Response Table Format

```markdown
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | uuid | — | The unique identifier of the Account |
| name | string | Yes | The display name of the Account (max 255 chars) |
| status | enum | — | Account status: `ACTIVE`, `INACTIVE`, `BLOCKED` |
```

Use `—` for response-only fields. Mark deprecated fields: `**[Deprecated]** Use \`route\` instead`

## Data Types Reference

| Type | Description | Example |
|------|-------------|---------|
| `uuid` | UUID v4 identifier | `3172933b-50d2-4b17-96aa-9b378d6a6eac` |
| `string` | Text value | `"Customer Account"` |
| `integer` | Whole number | `42` |
| `boolean` | True/false | `true` |
| `timestamptz` | ISO 8601 (UTC) | `2024-01-15T10:30:00Z` |
| `jsonb` | JSON object | `{"key": "value"}` |
| `array` | List of values | `["item1", "item2"]` |
| `enum` | Predefined values | `currency`, `crypto` |

## Errors

Standard format:
```json
{
  "code": "ACCOUNT_NOT_FOUND",
  "message": "The specified account does not exist",
  "details": { "accountId": "invalid-uuid" }
}
```

Error table:

| Status | Code | Description | Resolution |
|--------|------|-------------|------------|
| 400 | INVALID_REQUEST | Validation failed | Check request format |
| 401 | UNAUTHORIZED | Missing/invalid auth | Provide valid API key |
| 403 | FORBIDDEN | Insufficient permissions | Contact admin |
| 404 | NOT_FOUND | Resource doesn't exist | Verify resource ID |
| 409 | CONFLICT | Resource already exists | Use different identifier |
| 422 | UNPROCESSABLE_ENTITY | Business rule violation | Check constraints |
| 500 | INTERNAL_ERROR | Server error | Retry or contact support |

## HTTP Status Codes

**Success:** 200 (GET/PUT/PATCH), 201 (POST creates), 204 (DELETE)

**Client errors:** 400 (malformed), 401 (no auth), 403 (no permission), 404 (not found), 409 (conflict), 422 (invalid semantics)

**Server errors:** 500 (internal)

## Example Endpoint Documentation

```markdown
## Create Account

Create a new Account in a Ledger.

**POST** `/v1/organizations/{orgId}/ledgers/{ledgerId}/accounts`

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| orgId | uuid | Yes | Organization ID |
| ledgerId | uuid | Yes | Ledger ID |

### Request Body

```json
{
  "name": "My Bank Account",
  "code": "ACC001",
  "status": "ACTIVE"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Display name (max 255 chars) |
| code | string | Yes | Account code (max 50 chars, uppercase) |
| status | enum | No | `ACTIVE`, `INACTIVE`. Default: `ACTIVE` |

### Success Response

**200 OK**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My Bank Account",
  "code": "ACC001",
  "status": "ACTIVE",
  "createdAt": "2024-01-15T10:30:00Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | The unique identifier of the Account |
| name | string | The display name of the Account |
| code | string | The account code |
| status | enum | Account status: `ACTIVE`, `INACTIVE`, `BLOCKED` |
| createdAt | timestamptz | Timestamp of creation (UTC) |

### Errors

| Status | Code | Description |
|--------|------|-------------|
| 400 | INVALID_REQUEST | Validation failed (e.g., missing name) |
| 401 | UNAUTHORIZED | Missing or invalid API key |
| 409 | CONFLICT | Account code already exists in this Ledger |
| 500 | INTERNAL_ERROR | Server error |
```

## Pagination

For paginated endpoints, document:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 10 | Results per page (max 100) |
| page | integer | 1 | Page number |

Response: `items`, `page`, `limit`, `totalItems`, `totalPages`

## Quality Checklist

- [ ] HTTP method and path correct
- [ ] All path parameters documented
- [ ] All query parameters documented
- [ ] All request body fields documented with types
- [ ] All response fields documented with types
- [ ] Required vs optional clear
- [ ] Realistic request/response examples included
- [ ] All error codes documented
- [ ] Deprecated fields marked
- [ ] Links to related endpoints included
