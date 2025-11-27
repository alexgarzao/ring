# YAML Schema Reference for Solution Documentation

This document describes the YAML frontmatter schema used in solution documentation files created by the `codify-solution` skill.

## Required Fields

### `date`
- **Type:** String (ISO date format)
- **Pattern:** `YYYY-MM-DD`
- **Example:** `2025-01-27`
- **Purpose:** When the problem was solved

### `problem_type`
- **Type:** Enum
- **Values:**
  - `build_error` - Compilation, bundling, or build process failures
  - `test_failure` - Unit, integration, or E2E test failures
  - `runtime_error` - Errors occurring during execution
  - `performance_issue` - Slow queries, memory leaks, latency
  - `database_issue` - Migration, query, or data integrity problems
  - `security_issue` - Vulnerabilities, auth problems, data exposure
  - `ui_bug` - Visual glitches, interaction problems
  - `integration_issue` - API, service communication, third-party
  - `logic_error` - Incorrect behavior, wrong calculations
  - `dependency_issue` - Package conflicts, version mismatches
  - `configuration_error` - Environment, settings, config files
  - `workflow_issue` - CI/CD, deployment, process problems
- **Purpose:** Determines storage directory and enables filtering

### `component`
- **Type:** String (free-form)
- **Example:** `auth-service`, `payment-gateway`, `user-dashboard`
- **Purpose:** Identifies the affected module/service
- **Note:** Not an enum - varies by project

### `symptoms`
- **Type:** Array of strings (1-5 items)
- **Example:**
  ```yaml
  symptoms:
    - "Error: Cannot read property 'id' of undefined"
    - "Login button unresponsive after 3 clicks"
  ```
- **Purpose:** Observable error messages or behaviors for searchability

### `root_cause`
- **Type:** Enum
- **Values:**
  - `missing_dependency` - Required package/module not installed
  - `wrong_api_usage` - Incorrect use of library/framework API
  - `configuration_error` - Wrong settings or environment variables
  - `logic_error` - Bug in business logic or algorithms
  - `race_condition` - Timing-dependent bug
  - `memory_issue` - Leaks, excessive allocation
  - `type_mismatch` - Wrong type passed or returned
  - `missing_validation` - Input not properly validated
  - `permission_error` - Access denied, wrong credentials
  - `environment_issue` - Dev/prod differences, missing tools
  - `version_incompatibility` - Breaking changes between versions
  - `data_corruption` - Invalid or inconsistent data state
  - `missing_error_handling` - Unhandled exceptions/rejections
  - `incorrect_assumption` - Wrong mental model of system
- **Purpose:** Enables pattern detection across similar issues

### `resolution_type`
- **Type:** Enum
- **Values:**
  - `code_fix` - Changed source code
  - `config_change` - Updated configuration files
  - `dependency_update` - Updated/added/removed packages
  - `migration` - Database or data migration
  - `test_fix` - Fixed test code (not production code)
  - `environment_setup` - Changed environment/infrastructure
  - `documentation` - Solution was documenting existing behavior
  - `workaround` - Temporary fix, not ideal solution
- **Purpose:** Categorizes the type of change made

### `severity`
- **Type:** Enum
- **Values:** `critical`, `high`, `medium`, `low`
- **Purpose:** Original impact severity for prioritization analysis

## Optional Fields

### `project`
- **Type:** String
- **Example:** `midaz`
- **Purpose:** Project identifier (auto-detected from git)

### `language`
- **Type:** String
- **Example:** `go`, `typescript`, `python`
- **Purpose:** Primary language involved for filtering

### `framework`
- **Type:** String
- **Example:** `gin`, `nextjs`, `fastapi`
- **Purpose:** Framework-specific issues for filtering

### `tags`
- **Type:** Array of strings (max 8)
- **Example:** `[authentication, jwt, middleware, rate-limiting]`
- **Purpose:** Free-form keywords for discovery

### `related_issues`
- **Type:** Array of strings
- **Example:**
  ```yaml
  related_issues:
    - "docs/solutions/security-issues/jwt-expiry-20250115.md"
    - "https://github.com/org/repo/issues/123"
  ```
- **Purpose:** Cross-reference related solutions or external issues

## Category to Directory Mapping

| `problem_type` | Directory |
|----------------|-----------|
| `build_error` | `docs/solutions/build-errors/` |
| `test_failure` | `docs/solutions/test-failures/` |
| `runtime_error` | `docs/solutions/runtime-errors/` |
| `performance_issue` | `docs/solutions/performance-issues/` |
| `database_issue` | `docs/solutions/database-issues/` |
| `security_issue` | `docs/solutions/security-issues/` |
| `ui_bug` | `docs/solutions/ui-bugs/` |
| `integration_issue` | `docs/solutions/integration-issues/` |
| `logic_error` | `docs/solutions/logic-errors/` |
| `dependency_issue` | `docs/solutions/dependency-issues/` |
| `configuration_error` | `docs/solutions/configuration-errors/` |
| `workflow_issue` | `docs/solutions/workflow-issues/` |

## Validation Rules

1. **All required fields must be present**
2. **Enum values must match exactly** (case-sensitive)
3. **Date must be valid ISO format**
4. **Symptoms array must have 1-5 items**
5. **Tags array limited to 8 items**

## Example Complete Frontmatter

```yaml
---
date: 2025-01-27
problem_type: runtime_error
component: auth-middleware
symptoms:
  - "Error: JWT malformed"
  - "401 Unauthorized on valid tokens"
root_cause: wrong_api_usage
resolution_type: code_fix
severity: high
project: midaz
language: go
framework: gin
tags:
  - authentication
  - jwt
  - middleware
related_issues:
  - "docs/solutions/security-issues/jwt-refresh-logic-20250110.md"
---
```
