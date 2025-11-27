---
name: api-field-descriptions
description: |
  Patterns for writing clear, consistent API field descriptions including
  types, constraints, examples, and edge cases.

trigger: |
  - Writing API field documentation
  - Documenting request/response schemas
  - Creating data model documentation

skip_when: |
  - Writing conceptual docs → use writing-functional-docs
  - Full API endpoint docs → use writing-api-docs

related:
  complementary: [writing-api-docs]
---

# API Field Descriptions

Field descriptions are the most-read part of API documentation. Users scan for specific fields and need clear, consistent information.

---

## Field Description Structure

Every field description should answer:

1. **What is it?** – The field's purpose
2. **What type?** – Data type and format
3. **Required?** – Is it mandatory?
4. **Constraints?** – Limits, validations, formats
5. **Example?** – What does valid data look like?

---

## Basic Field Description Format

### Table Format (Preferred)

```markdown
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | uuid | — | The unique identifier of the Account |
| name | string | Yes | The display name of the Account (max 255 chars) |
| status | enum | — | Account status: `ACTIVE`, `INACTIVE`, `BLOCKED` |
```

**Note:** Use `—` for response-only fields (not applicable for requests).

### Nested Object Format

```markdown
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| status | object | — | Account status information |
| status.code | string | — | Status code: `ACTIVE`, `INACTIVE`, `BLOCKED` |
| status.description | string | — | Optional human-readable description |
```

---

## Description Patterns by Type

### UUID Fields

```markdown
| id | uuid | — | The unique identifier of the Account |
| organizationId | uuid | Yes | The unique identifier of the Organization |
```

Pattern: "The unique identifier of the [Entity]"

---

### String Fields

**Simple string:**
```markdown
| name | string | Yes | The display name of the Account |
```

**String with constraints:**
```markdown
| code | string | Yes | The asset code (max 10 chars, uppercase, e.g., "BRL") |
| alias | string | No | A user-friendly identifier (must start with @) |
```

**String with format:**
```markdown
| email | string | Yes | Email address (e.g., "user@example.com") |
| phone | string | No | Phone number in E.164 format (e.g., "+5511999999999") |
```

---

### Enum Fields

```markdown
| type | enum | Yes | Asset type: `currency`, `crypto`, `commodity`, `others` |
| status | enum | — | Transaction status: `pending`, `completed`, `reversed` |
```

Pattern: "[Field purpose]: `value1`, `value2`, `value3`"

Always list all valid values in backticks.

---

### Boolean Fields

```markdown
| allowSending | boolean | No | If `true`, sending transactions is permitted. Default: `true` |
| allowReceiving | boolean | No | If `true`, receiving transactions is permitted. Default: `true` |
```

Pattern: "If `true`, [what happens]. Default: `[value]`"

---

### Numeric Fields

**Integer:**
```markdown
| version | integer | — | Balance version, incremented with each transaction |
| limit | integer | No | Results per page (1-100). Default: 10 |
```

**With range:**
```markdown
| scale | integer | Yes | Decimal places for the asset (0-18) |
```

---

### Timestamp Fields

```markdown
| createdAt | timestamptz | — | Timestamp of creation (UTC) |
| updatedAt | timestamptz | — | Timestamp of last update (UTC) |
| deletedAt | timestamptz | — | Timestamp of soft deletion, if applicable (UTC) |
```

Pattern: "Timestamp of [event] (UTC)"

Always specify UTC.

---

### Object Fields (JSONB)

```markdown
| metadata | jsonb | No | Key-value pairs for custom data |
| status | jsonb | — | Status information including code and description |
| address | jsonb | No | Address information (street, city, country, postalCode) |
```

For complex objects, document child fields separately or link to schema.

---

### Array Fields

```markdown
| source | array | Yes | List of source account aliases |
| operations | array | — | List of operations in the transaction |
| tags | array | No | List of string tags for categorization |
```

Specify what the array contains.

---

## Required vs Optional

### In Request Documentation

| Indicator | Meaning |
|-----------|---------|
| Yes | Field must be provided |
| No | Field is optional |
| Conditional | Required in specific scenarios (explain in description) |

**Conditional example:**
```markdown
| portfolioId | uuid | Conditional | Required when creating customer accounts |
```

### In Response Documentation

Response fields don't have "Required" – they're always returned (or null).

Use `—` in the Required column for response-only fields.

---

## Default Values

Always document defaults for optional fields:

```markdown
| limit | integer | No | Results per page. Default: 10 |
| allowSending | boolean | No | Permit sending. Default: `true` |
| type | string | No | Account type. Default: none (untyped) |
```

---

## Nullable Fields

Indicate when fields can be null:

```markdown
| deletedAt | timestamptz | — | Soft deletion timestamp, or `null` if not deleted |
| description | string | No | Optional description, or `null` if not provided |
| parentAccountId | uuid | No | Parent account ID, or `null` for root accounts |
```

---

## Deprecated Fields

Mark deprecated fields clearly:

```markdown
| chartOfAccounts | string | No | **[Deprecated]** Use `route` instead |
```

Or with more context:

```markdown
| chartOfAccountsGroupName | string | — | **[Deprecated]** This field is present for backward compatibility. Use `route` for new integrations. |
```

---

## Read-Only Fields

Indicate fields that can't be set by the client:

```markdown
| id | uuid | — | **Read-only.** Generated by the system |
| createdAt | timestamptz | — | **Read-only.** Set automatically on creation |
| version | integer | — | **Read-only.** Incremented automatically |
```

---

## Field Relationship Descriptions

When fields relate to other entities:

```markdown
| ledgerId | uuid | Yes | The unique identifier of the Ledger this account belongs to |
| portfolioId | uuid | No | The Portfolio grouping this account. See [Portfolios](link) |
| assetCode | string | Yes | References an Asset code. Must exist in the Ledger |
```

---

## Writing Good Descriptions

### Be Specific

| Vague | Specific |
|-------|----------|
| The name | The display name of the Account |
| Status info | Account status: `ACTIVE`, `INACTIVE`, `BLOCKED` |
| A number | Balance version, incremented with each transaction |

### Include Constraints

| Missing Constraints | With Constraints |
|--------------------|------------------|
| The code | The asset code (max 10 chars, uppercase) |
| Page number | Page number (starts at 1) |
| Amount | Amount in smallest unit (e.g., cents for BRL) |

### Add Context

| No Context | With Context |
|------------|--------------|
| The timestamp | Timestamp of creation (UTC) |
| Account ID | The Account receiving the funds |
| Parent ID | Parent account for hierarchical structures |

---

## Quality Checklist

For each field, verify:

- [ ] Description explains the field's purpose
- [ ] Data type is accurate
- [ ] Required/optional status is clear
- [ ] Constraints are documented (max length, valid values)
- [ ] Default value noted (if optional)
- [ ] Nullable behavior explained (if applicable)
- [ ] Deprecated fields are marked
- [ ] Read-only fields are indicated
- [ ] Relationships to other entities are clear
- [ ] Example values are realistic
