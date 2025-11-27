---
name: codify-solution
description: |
  Capture solved problems as structured documentation - auto-triggers when user
  confirms fix worked. Creates searchable knowledge base in docs/solutions/.
  The compounding effect: each documented solution makes future debugging faster.

trigger: |
  - User confirms fix worked ("that worked", "it's fixed", "solved it")
  - /ring-default:codify command invoked manually
  - Non-trivial debugging completed (multiple investigation attempts)
  - After systematic-debugging Phase 4 succeeds

skip_when: |
  - Simple typo or obvious syntax error (< 2 min to fix)
  - Solution already documented in docs/solutions/
  - Trivial fix that won't recur
  - User declines documentation

sequence:
  after: [systematic-debugging, root-cause-tracing]

related:
  similar: [writing-plans]  # writing-plans is for implementation planning, codify-solution is for solved problems
  complementary: [systematic-debugging, writing-plans, test-driven-development]

compliance_rules:
  - id: "docs_directory_exists"
    description: "Solution docs directory must exist or be creatable"
    check_type: "command_output"
    command: "test -d docs/solutions/ || mkdir -p docs/solutions/"
    severity: "blocking"
    failure_message: "Cannot access docs/solutions/. Check permissions."

  - id: "required_context_gathered"
    description: "All required context fields must be populated before doc creation"
    check_type: "manual_verification"
    required_fields:
      - component
      - symptoms
      - root_cause
      - solution
    severity: "blocking"
    failure_message: "Missing required context. Ask user for: component, symptoms, root_cause, solution."

  - id: "schema_validation"
    description: "YAML frontmatter must pass schema validation"
    check_type: "schema_validation"
    schema_path: "schema.yaml"
    severity: "blocking"
    failure_message: "Schema validation failed. Check problem_type, root_cause, resolution_type enum values."

prerequisites:
  - name: "docs_directory_writable"
    check: "test -w docs/ || mkdir -p docs/solutions/"
    failure_message: "Cannot write to docs/. Check permissions."
    severity: "blocking"

composition:
  works_well_with:
    - skill: "systematic-debugging"
      when: "debugging session completed successfully"
      transition: "Automatically suggest codify after Phase 4 verification"

    - skill: "writing-plans"
      when: "planning new feature implementation"
      transition: "Search docs/solutions/ for prior related issues during planning"

    - skill: "test-driven-development"
      when: "writing tests for bug fixes"
      transition: "After test passes, document the solution for future reference"

  conflicts_with: []

  typical_workflow: |
    1. Debugging session completes (systematic-debugging Phase 4)
    2. User confirms fix worked
    3. Auto-suggest codify-solution via hook
    4. Gather context from conversation
    5. Validate schema and create documentation
    6. Cross-reference with related solutions
---

# Codify Solution Skill

**Purpose:** Build searchable institutional knowledge by capturing solved problems immediately after confirmation.

**The Compounding Effect:**
```
First time solving issue → Research (30 min)
Document the solution   → docs/solutions/{category}/ (5 min)
Next similar issue      → Quick lookup (2 min)
Knowledge compounds     → Team gets smarter over time
```

---

## 7-Step Process

### Step 1: Detect Confirmation

**Auto-invoke after phrases:**
- "that worked"
- "it's fixed", "fixed it"
- "working now"
- "problem solved", "solved it"
- "that did it"
- "all good now"
- "issue resolved"

**Criteria for documentation (ALL must apply):**
- Non-trivial problem (took multiple attempts to solve)
- Solution is not immediately obvious
- Future sessions would benefit from having this documented
- User hasn't declined

**If triggered automatically:**
> "It looks like you've solved a problem! Would you like to document this solution for future reference?
>
> Run: `/ring-default:codify`
> Or say: 'yes, document this'"

---

### Step 2: Gather Context

Extract from conversation history:

| Field | Description | Source |
|-------|-------------|--------|
| **Title** | Document title for H1 heading | Derived: "[Primary Symptom] in [Component]" |
| **Component** | Which module/file had the problem | File paths mentioned |
| **Symptoms** | Observable error/behavior | Error messages, logs |
| **Investigation** | What was tried and failed | Conversation history |
| **Root Cause** | Technical explanation | Analysis performed |
| **Solution** | What fixed it | Code changes made |
| **Prevention** | How to avoid in future | Lessons learned |

**BLOCKING GATE:**
If ANY critical context is missing, ask the user and WAIT for response:

```
Missing context for documentation:
- [ ] Component: Which module/service was affected?
- [ ] Symptoms: What was the exact error message?
- [ ] Root Cause: What was the underlying cause?

Please provide the missing information before I create the documentation.
```

---

### Step 3: Check Existing Docs

**First, ensure docs/solutions/ exists:**
```bash
# Initialize directory structure if needed
mkdir -p docs/solutions/
```

Search `docs/solutions/` for similar issues:

```bash
# Search for similar symptoms
grep -r "exact error phrase" docs/solutions/ 2>/dev/null || true

# Search by component
grep -r "component: similar-component" docs/solutions/ 2>/dev/null || true
```

**If similar found, present options:**

| Option | When to Use |
|--------|-------------|
| **1. Create new doc with cross-reference** | Different root cause but related symptoms (recommended) |
| **2. Update existing doc** | Same root cause, additional context to add |
| **3. Skip documentation** | Exact duplicate, no new information |

---

### Step 4: Generate Filename

**Format:** `[sanitized-symptom]-[component]-[YYYYMMDD].md`

**Sanitization rules:**
1. Convert to lowercase
2. Replace spaces with hyphens
3. Remove special characters (keep alphanumeric and hyphens)
4. Truncate to < 80 characters total
5. **Ensure unique** - check for existing files:

```bash
# Get category directory from problem_type
CATEGORY_DIR=$(get_category_directory "$PROBLEM_TYPE")

# Check for filename collision
BASE_NAME="sanitized-symptom-component-YYYYMMDD"
FILENAME="${BASE_NAME}.md"
COUNTER=2

while [ -f "docs/solutions/${CATEGORY_DIR}/${FILENAME}" ]; do
    FILENAME="${BASE_NAME}-${COUNTER}.md"
    COUNTER=$((COUNTER + 1))
done
```

**Examples:**
```
cannot-read-property-id-auth-service-20250127.md
jwt-malformed-error-middleware-20250127.md
n-plus-one-query-user-api-20250127.md
# If duplicate exists:
jwt-malformed-error-middleware-20250127-2.md
```

---

### Step 5: Validate YAML Schema

**CRITICAL GATE:** Load `schema.yaml` and validate all required fields.

**Required fields checklist:**
- [ ] `date` - Format: YYYY-MM-DD
- [ ] `problem_type` - Must be valid enum value
- [ ] `component` - Non-empty string
- [ ] `symptoms` - Array with 1-5 items
- [ ] `root_cause` - Must be valid enum value
- [ ] `resolution_type` - Must be valid enum value
- [ ] `severity` - Must be: critical, high, medium, or low

**BLOCK if validation fails:**
```
Schema validation failed:
- problem_type: "database" is not valid. Use one of: build_error, test_failure,
  runtime_error, performance_issue, database_issue, ...
- symptoms: Must have at least 1 item

Please correct these fields before proceeding.
```

**Valid `problem_type` values:**
- build_error, test_failure, runtime_error, performance_issue
- database_issue, security_issue, ui_bug, integration_issue
- logic_error, dependency_issue, configuration_error, workflow_issue

**Valid `root_cause` values:**
- missing_dependency, wrong_api_usage, configuration_error, logic_error
- race_condition, memory_issue, type_mismatch, missing_validation
- permission_error, environment_issue, version_incompatibility
- data_corruption, missing_error_handling, incorrect_assumption

**Valid `resolution_type` values:**
- code_fix, config_change, dependency_update, migration
- test_fix, environment_setup, documentation, workaround

---

### Step 6: Create Documentation

1. **Ensure directory exists:**
   ```bash
   mkdir -p docs/solutions/{category}/
   ```

2. **Load template:** Read `assets/resolution-template.md`

3. **Fill placeholders:**
   - Replace all `{{FIELD}}` placeholders with gathered context
   - Ensure code blocks have correct language tags
   - Format tables properly

   **Placeholder Syntax:**
   - `{{FIELD}}` - Required field, must be replaced with actual value
   - `{{FIELD|default}}` - Optional field, use default value if not available
   - Remove unused optional field lines entirely (e.g., empty symptom slots)

4. **Write file:**
   ```bash
   # Path: docs/solutions/{category}/{filename}.md
   ```

5. **Verify creation:**
   ```bash
   ls -la docs/solutions/{category}/{filename}.md
   ```

**Category to directory mapping (MANDATORY):**

```bash
# Category mapping function - use this EXACTLY
get_category_directory() {
    local problem_type="$1"
    case "$problem_type" in
        build_error) echo "build-errors" ;;
        test_failure) echo "test-failures" ;;
        runtime_error) echo "runtime-errors" ;;
        performance_issue) echo "performance-issues" ;;
        database_issue) echo "database-issues" ;;
        security_issue) echo "security-issues" ;;
        ui_bug) echo "ui-bugs" ;;
        integration_issue) echo "integration-issues" ;;
        logic_error) echo "logic-errors" ;;
        dependency_issue) echo "dependency-issues" ;;
        configuration_error) echo "configuration-errors" ;;
        workflow_issue) echo "workflow-issues" ;;
        *) echo "INVALID_CATEGORY"; return 1 ;;
    esac
}
```

| problem_type | Directory |
|--------------|-----------|
| build_error | build-errors |
| test_failure | test-failures |
| runtime_error | runtime-errors |
| performance_issue | performance-issues |
| database_issue | database-issues |
| security_issue | security-issues |
| ui_bug | ui-bugs |
| integration_issue | integration-issues |
| logic_error | logic-errors |
| dependency_issue | dependency-issues |
| configuration_error | configuration-errors |
| workflow_issue | workflow-issues |

**CRITICAL:** If `problem_type` is not in this list, **BLOCK** and ask user to select valid category.

6. **Confirm creation:**
   ```
   ✅ Solution documented: docs/solutions/{category}/{filename}.md

   File created with {N} required fields and {M} optional fields populated.
   ```

---

### Step 7: Post-Documentation Options

Present decision menu after successful creation:

```
Solution documented: docs/solutions/{category}/{filename}.md

What would you like to do next?
1. Continue with current workflow
2. Promote to Critical Pattern (if recurring issue)
3. Link to related issues
4. View the documentation
5. Search for similar issues
```

**Option 2: Promote to Critical Pattern**
If this issue has occurred multiple times or is particularly important:
1. Ensure directory exists: `mkdir -p docs/solutions/patterns/`
2. Load `assets/critical-pattern-template.md`
3. Create in `docs/solutions/patterns/`
4. Link all related instance docs

**Option 3: Link to related issues**
- Search for related docs
- Add to `related_issues` field in YAML frontmatter
- Update the related doc to cross-reference this one

---

## Integration Points

### With systematic-debugging

After Phase 4 (Verification) succeeds, suggest:
> "The fix has been verified. Would you like to document this solution for future reference?
> Run: `/ring-default:codify`"

### With writing-plans

During planning phase, search existing solutions:
```bash
# Before designing a feature, check for known issues
grep -r "component: {related-component}" docs/solutions/
```

### With pre-dev workflow

In Gate 1 (PRD Creation), reference existing solutions:
- Search `docs/solutions/` for related prior art
- Include relevant learnings in requirements

---

## Solution Doc Search Patterns

**Search by error message:**
```bash
grep -r "exact error text" docs/solutions/
```

**Search by component:**
```bash
grep -r "component: auth" docs/solutions/
```

**Search by root cause:**
```bash
grep -r "root_cause: race_condition" docs/solutions/
```

**Search by tag:**
```bash
grep -r "- authentication" docs/solutions/
```

**List all by category:**
```bash
ls docs/solutions/performance-issues/
```

---

## Rationalization Defenses

| Excuse | Counter |
|--------|---------|
| "This was too simple to document" | If it took > 5 min to solve, document it |
| "I'll remember this" | You won't. Your future self will thank you. |
| "Nobody else will hit this" | They will. And they'll spend 30 min re-investigating. |
| "The code is self-documenting" | The investigation process isn't in the code |
| "I'll do it later" | No you won't. Do it now while context is fresh. |

---

## Success Metrics

A well-documented solution should:
- [ ] Be findable via grep search on symptoms
- [ ] Have clear root cause explanation
- [ ] Include before/after code examples
- [ ] List prevention strategies
- [ ] Take < 5 minutes to write (use template)

---

## Example Output

**File:** `docs/solutions/runtime-errors/jwt-malformed-auth-middleware-20250127.md`

```markdown
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
---

# JWT Malformed Error in Auth Middleware

## Problem

Valid JWTs were being rejected with "JWT malformed" error after
upgrading the jwt-go library.

### Symptoms

- "Error: JWT malformed" on all authenticated requests
- 401 Unauthorized responses for valid tokens
- Started after dependency update

## Investigation

### What didn't work

1. Regenerating tokens - same error
2. Checking token format - tokens were valid

### Root Cause

The new jwt-go version changed the default parser behavior.
The `ParseWithClaims` function now requires explicit algorithm
specification.

## Solution

Added explicit algorithm in parser options:

```go
// Before
token, err := jwt.ParseWithClaims(tokenString, claims, keyFunc)

// After
token, err := jwt.ParseWithClaims(tokenString, claims, keyFunc,
    jwt.WithValidMethods([]string{"HS256"}))
```

## Prevention

1. Read changelogs before upgrading auth-related dependencies
2. Add integration tests for token parsing
3. Pin major versions of security-critical packages
```
