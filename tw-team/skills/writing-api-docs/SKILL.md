---
name: writing-api-docs
description: |
  Patterns and structure for writing API reference documentation including
  endpoint descriptions, request/response schemas, and error documentation.

trigger: |
  - Documenting REST API endpoints
  - Writing request/response examples
  - Documenting error codes
  - Creating API field descriptions

skip_when: |
  - Writing conceptual guides → use writing-functional-docs
  - Reviewing documentation → use documentation-review
  - Writing code → use dev-team agents

sequence:
  before: [documentation-review]

related:
  similar: [writing-functional-docs]
  complementary: [api-field-descriptions, documentation-structure]
---

# Writing API Reference Documentation

API reference documentation describes what each endpoint does, its parameters, request/response formats, and error conditions. It focuses on the "what" rather than the "why."

---

## API Reference Principles

### RESTful and Predictable
- Follow standard HTTP methods and status codes
- Use consistent URL patterns
- Document idempotency behavior

### Consistent Formats
- Requests and responses use JSON
- Clear typing and structures
- Standard error format

### Explicit Versioning
- Document version in URL path
- Note backward compatibility
- Mark deprecated fields clearly

---

## Endpoint Documentation Structure

### Basic Structure

```markdown
# Endpoint Name

Brief description of what this endpoint does.

## Request

### HTTP Method and Path

`POST /v1/organizations/{organizationId}/ledgers/{ledgerId}/accounts`

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| organizationId | uuid | Yes | The unique identifier of the Organization |
| ledgerId | uuid | Yes | The unique identifier of the Ledger |

### Request Body

```json
{
  "name": "string",
  "assetCode": "string",
  "type": "string"
}
```

### Request Body Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | The name of the Account |
| assetCode | string | Yes | The code of the Asset (e.g., "BRL", "USD") |
| type | string | No | The account type classification |

## Response

### Success Response (201 Created)

```json
{
  "id": "3172933b-50d2-4b17-96aa-9b378d6a6eac",
  "name": "Customer Account",
  "assetCode": "BRL",
  "status": {
    "code": "ACTIVE"
  },
  "createdAt": "2024-01-15T10:30:00Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| id | uuid | The unique identifier of the created Account |
| name | string | The name of the Account |
| createdAt | timestamptz | Timestamp of creation (UTC) |

## Errors

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | INVALID_REQUEST | Request body validation failed |
| 404 | LEDGER_NOT_FOUND | The specified Ledger does not exist |
| 409 | ACCOUNT_EXISTS | An account with this alias already exists |
```

---

## Field Description Patterns

### Basic Field Description

```markdown
| name | string | The name of the Account |
```

### Field with Constraints

```markdown
| code | string | The asset code (max 10 characters, uppercase) |
```

### Field with Example

```markdown
| email | string | User email address (e.g., "user@example.com") |
```

### Required vs Optional

```markdown
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | The name of the Account |
| alias | string | No | A user-friendly identifier. If omitted, uses the account ID |
```

### Deprecated Fields

```markdown
| chartOfAccountsGroupName | string | **[Deprecated]** Use `route` instead. The name of the group. |
```

---

## Data Types Reference

Use consistent type names across all documentation:

| Type | Description | Example |
|------|-------------|---------|
| `uuid` | UUID v4 identifier | `3172933b-50d2-4b17-96aa-9b378d6a6eac` |
| `string` | Text value | `"Customer Account"` |
| `text` | Long text value | `"Detailed description..."` |
| `integer` | Whole number | `42` |
| `boolean` | True/false value | `true` |
| `timestamptz` | ISO 8601 timestamp (UTC) | `2024-01-15T10:30:00Z` |
| `jsonb` | JSON object | `{"key": "value"}` |
| `array` | List of values | `["item1", "item2"]` |
| `enum` | One of predefined values | `currency`, `crypto`, `commodity` |

---

## Request/Response Examples

### Complete Request Example

Always show a realistic, working example:

```json
{
  "name": "João Silva - Checking",
  "assetCode": "BRL",
  "type": "checking",
  "alias": "@joao_checking",
  "metadata": {
    "customerId": "cust_123456",
    "branch": "0001"
  }
}
```

### Complete Response Example

Show all fields that would be returned:

```json
{
  "id": "3172933b-50d2-4b17-96aa-9b378d6a6eac",
  "organizationId": "7c3e4f2a-1b8d-4e5c-9f0a-2d3e4f5a6b7c",
  "ledgerId": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "name": "João Silva - Checking",
  "assetCode": "BRL",
  "type": "checking",
  "alias": "@joao_checking",
  "status": {
    "code": "ACTIVE",
    "description": null
  },
  "metadata": {
    "customerId": "cust_123456",
    "branch": "0001"
  },
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z",
  "deletedAt": null
}
```

---

## Error Documentation

### Standard Error Format

```json
{
  "code": "ACCOUNT_NOT_FOUND",
  "message": "The specified account does not exist",
  "details": {
    "accountId": "invalid-uuid"
  }
}
```

### Error Table Format

| Status Code | Error Code | Description | Resolution |
|-------------|------------|-------------|------------|
| 400 | INVALID_REQUEST | Request validation failed | Check request body format |
| 401 | UNAUTHORIZED | Missing or invalid authentication | Provide valid API key |
| 403 | FORBIDDEN | Insufficient permissions | Contact admin for access |
| 404 | NOT_FOUND | Resource does not exist | Verify the resource ID |
| 409 | CONFLICT | Resource already exists | Use a different identifier |
| 422 | UNPROCESSABLE_ENTITY | Business rule violation | Check business constraints |
| 500 | INTERNAL_ERROR | Server error | Retry or contact support |

---

## HTTP Status Codes

### Success Codes

| Code | Usage |
|------|-------|
| 200 OK | Successful GET, PUT, PATCH |
| 201 Created | Successful POST that creates a resource |
| 204 No Content | Successful DELETE |

### Error Codes

| Code | Usage |
|------|-------|
| 400 Bad Request | Malformed request syntax |
| 401 Unauthorized | Missing or invalid authentication |
| 403 Forbidden | Valid auth but insufficient permissions |
| 404 Not Found | Resource does not exist |
| 409 Conflict | Resource state conflict (e.g., duplicate) |
| 422 Unprocessable Entity | Valid syntax but invalid semantics |
| 429 Too Many Requests | Rate limit exceeded |
| 500 Internal Server Error | Server-side error |

---

## Pagination Documentation

When an endpoint returns paginated results:

```markdown
### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 10 | Number of results per page (max 100) |
| page | integer | 1 | Page number to retrieve |

### Pagination Response

```json
{
  "items": [...],
  "page": 1,
  "limit": 10,
  "totalItems": 150,
  "totalPages": 15
}
```
```

---

## API Versioning Notes

When documenting versioned APIs:

```markdown
> **Note:** You're viewing documentation for the **current version** (v3).
> For previous versions, use the version switcher.
```

For deprecated endpoints:

```markdown
> **Deprecated:** This endpoint will be removed in v4. Use [/v3/accounts](link) instead.
```

---

## Quality Checklist

Before finishing API documentation, verify:

- [ ] HTTP method and path are correct
- [ ] All path parameters documented
- [ ] All query parameters documented
- [ ] All request body fields documented with types
- [ ] All response fields documented with types
- [ ] Required vs optional fields are clear
- [ ] Realistic request/response examples included
- [ ] All error codes documented
- [ ] Deprecated fields are marked
- [ ] Links to related endpoints included
